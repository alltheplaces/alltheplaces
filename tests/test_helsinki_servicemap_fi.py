# -*- coding: utf-8 -*-
"""Behavioural tests for helsinki_servicemap_fi.

Each case pins a load-bearing rule: name splits, address parsing, category
precedence/refinement and operator/brand attribution. Cases use real feed
records (unit ids in comments, singular/plural/range/bracket forms all
count) unless marked SYNTHETIC, in which case the feed has no occurrence
and the input exercises a helper branch directly.
"""

from types import SimpleNamespace

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.government.helsinki_servicemap_fi import HelsinkiServicemapFiSpider


class _Stats:
    def __init__(self):
        self.d = {}

    def inc_value(self, key, n=1):
        self.d[key] = self.d.get(key, 0) + n

    def get_value(self, key, default=0):
        return self.d.get(key, default)


def make_spider(extra_parents=None):
    spider = HelsinkiServicemapFiSpider()
    spider.crawler = SimpleNamespace(stats=_Stats())
    spider.rule_precedence = {node_id: i for i, node_id in enumerate(spider.SERVICE_NODES)}
    spider.departments = {}
    spider.all_service_nodes = set(spider.SERVICE_NODES)
    spider.parent_service_node = dict(extra_parents or {})
    spider.seen_places = set()
    spider._build_service_graph()
    return spider


def named(spider, fi, service_nodes=(), sv=None, en=None):
    item = Feature()
    name = {"fi": fi}
    if sv is not None:
        name["sv"] = sv
    if en is not None:
        name["en"] = en
    spider._apply_name(item, {"name": name, "service_nodes": list(service_nodes)})
    return item


def addressed(spider, address):
    item = Feature()
    spider._apply_street_address(item, address)
    return item


def categorised(spider, fi, service_nodes):
    item = Feature()
    unit = {"name": {"fi": fi}, "service_nodes": list(service_nodes)}
    spider._apply_name(item, unit)
    spider._apply_category(item, unit)
    return item


def full(spider, fi, service_nodes):
    # Name plus category, as _build_item applies them.
    return categorised(spider, fi, service_nodes)


def operated(category, unit, departments=None):
    spider = make_spider()
    if departments:
        spider.departments = departments
    item = Feature()
    apply_category(category, item)
    spider._apply_operator(item, unit)
    return spider, item


def branded(unit):
    spider = make_spider()
    item = Feature()
    spider._apply_brand(item, unit)
    return item


def contacted(unit):
    spider = make_spider()
    item = Feature()
    spider._apply_contact(item, unit)
    return item


def parked(name_fi, desc_fi):
    spider = make_spider()
    item = Feature()
    apply_category(Categories.PARKING, item)
    spider._apply_parking_capacity(item, {"name": {"fi": name_fi}, "description": {"fi": desc_fi}})
    return item


def subtagged(name_fi, category):
    spider = make_spider()
    item = Feature()
    spider._apply_subtags(item, {"name": {"fi": name_fi}}, category)
    return item


# ---- Quadrant A: name splitting and cleaning -----------------------------
# Quadrants mirror the spider's pipeline sections: A names, B addresses,
# C categories, D operator/brand/contact/filters. Helpers (named,
# addressed, categorised) test one _apply_* in isolation; full() runs
# name+category as _build_item applies them. Helper-level cases (records
# _build_item would drop: NOT_DISPLAYED, excluded, no coords) pin the
# helper branch only and must stay helper-level: promoting them to full()
# or _build_item returns None by design.


def test_slash_splits_facility_into_venue():
    # Unit 80954: Vesalan liikuntapuisto / Pienpelikenttä 2.
    item = named(make_spider(), "Vesalan liikuntapuisto / Pienpelikenttä 2")
    assert item["name"] == "Pienpelikenttä 2"
    assert item["located_in"] == "Vesalan liikuntapuisto"
    assert item["extras"]["official_name"] == "Vesalan liikuntapuisto / Pienpelikenttä 2"


def test_slash_cultural_venue():
    # Unit 80688: Stoa / Musiikkisali.
    item = named(make_spider(), "Stoa / Musiikkisali")
    assert item["name"] == "Musiikkisali"
    assert item["located_in"] == "Stoa"


def test_bare_and_spaced_slash_combined_schools_stay_whole():
    # SYNTHETIC combined-school slash pairs.
    spider = make_spider()
    for raw in ("Karkkilan yläaste/lukio", "A yläaste / lukio"):
        assert spider._split_facility(raw) == (raw, None)


def test_ball_compounds_without_spaces_stay_whole():
    # SYNTHETIC sport-compound slash pair.
    assert make_spider()._split_facility("koripallo/lentopallo") == ("koripallo/lentopallo", None)


def test_activity_head_never_splits():
    # Unit 79883.
    item = named(make_spider(), "Iltapäivätoiminta / Leikkipuisto Rusettipuisto")
    assert item["name"] == "Iltapäivätoiminta / Leikkipuisto Rusettipuisto"
    assert "located_in" not in item


def test_ekopiste_chain_with_comma_address_tail():
    # Unit 71657 (helper-level: the record itself is NOT_DISPLAYED).
    item = named(make_spider(), "Ekopiste / Ekopunkt Selki, Selintie 515")
    assert item["name"] == "Ekopiste / Ekopunkt Selki"
    assert "located_in" not in item


def test_org_tail_stripped_from_activity_chain():
    # Unit 79856.
    item = named(make_spider(), "Iltapäivätoiminta / Aleksis Kiven peruskoulu, Beanet Oy")
    assert item["name"] == "Iltapäivätoiminta / Aleksis Kiven peruskoulu"
    assert item["extras"]["official_name"].endswith("Beanet Oy")


def test_institution_tails_reverse_to_service_first():
    # Units 69067 (sairaala) and perhekeskus-via-keskus: institution tails
    # are venues, not facilities; same convention, not default order.
    spider = make_spider()
    for raw, facility, venue in (
        ("Lasten toimintaterapia/Malmin sairaala", "Lasten toimintaterapia", "Malmin sairaala"),
        ("Lasten toimintaterapia/Vuosaaren perhekeskus", "Lasten toimintaterapia", "Vuosaaren perhekeskus"),
    ):
        item = named(spider, raw)
        assert item["name"] == facility, raw
        assert item["located_in"] == venue, raw


def test_comma_services_at_venues():
    # Units 78019 (playschool) and 78246 (päiväkoti): service-at-venue.
    spider = make_spider()
    for raw, service, venue in (
        (
            "Esiopetuksen opiskeluhuolto, Playschool Espoonlahti",
            "Esiopetuksen opiskeluhuolto",
            "Playschool Espoonlahti",
        ),
        (
            "Esiopetuksen opiskeluhuolto, Vanjärven päiväkoti",
            "Esiopetuksen opiskeluhuolto",
            "Vanjärven päiväkoti",
        ),
    ):
        item = named(spider, raw)
        assert item["name"] == service, raw
        assert item["located_in"] == venue, raw


def test_comma_street_tail_is_dropped():
    # Unit 80641.
    item = named(make_spider(), "Koskelan ala-asteen koulu, Mäkelänkatu 84")
    assert item["name"] == "Koskelan ala-asteen koulu"
    assert "located_in" not in item


def test_comma_esiopetus_group_without_venue_word_stays_whole():
    # Unit 73220: "esiopetusryhmät" is not a bare "esiopetus" tail.
    item = named(make_spider(), "Päiväkoti Koskela, esiopetusryhmät")
    assert item["name"] == "Päiväkoti Koskela, esiopetusryhmät"
    assert "located_in" not in item


def test_comma_esiopetus_head_wins():
    # Tuohimäen päiväkoti is unit 15443; the esiopetus tail is constructed.
    item = named(make_spider(), "Tuohimäen päiväkoti, esiopetus")
    assert item["name"] == "Tuohimäen päiväkoti"
    assert "located_in" not in item


def test_welfare_unit_named_after_host_school():
    # Unit 70287, all nodes in WELFARE_NODES.
    item = named(make_spider(), "Koivukylän koulu", [1374, 2350, 1375, 2164, 2165])
    assert item["name"] == "Opiskeluhuolto"
    assert item["located_in"] == "Koivukylän koulu"


def test_welfare_comma_form_keeps_service_head():
    # Unit 77974.
    item = named(make_spider(), "Opiskeluhuolto, Karkkilan yhteiskoulu", [1374, 2164])
    assert item["name"] == "Opiskeluhuolto"
    assert item["located_in"] == "Karkkilan yhteiskoulu"


def test_welfare_regex_rejects_koulu_prefix_compounds():
    # Constructed koulu-compounds; Suutarilan peruskoulu is unit 76239.
    spider = make_spider()
    unit = {"service_nodes": [2164]}
    assert spider._welfare_venue(unit, "Koulutuskeskus Salpaus") is None
    assert spider._welfare_venue(unit, "Koulukeskus") is None
    assert spider._welfare_venue(unit, "Eskola") is None
    assert spider._welfare_venue(unit, "Suutarilan peruskoulu") == "Suutarilan peruskoulu"


def test_vesiposti_comma_form_collapses():
    # Unit 75288.
    item = named(make_spider(), "Vesiposti, Kuninkaankartanontie")
    assert item["name"] == "Vesiposti"
    assert item["extras"]["official_name"] == "Vesiposti, Kuninkaankartanontie"


def test_vesiposti_space_and_paren_forms_collapse():
    # SYNTHETIC Vesiposti address variants.
    spider = make_spider()
    for raw in ("Vesiposti 1", "Vesiposti (Ylästöntie 71)", "Vesiposti/Ylästöntie 71"):
        assert named(spider, raw)["name"] == "Vesiposti"


def test_machine_name_trims_identifier_and_card_payment():
    # Unit 36286.
    item = named(make_spider(), "Pysäköintilippuautomaatti 591, Eläintarhantie / 1, korttimaksu")
    assert item["name"] == "Pysäköintilippuautomaatti 591"
    assert item["extras"]["payment:credit_cards"] == "yes"
    assert item["extras"]["payment:debit_cards"] == "yes"


def test_machine_name_coin_payment():
    # Unit 80604.
    item = named(make_spider(), "Pysäköintilippuautomaatti 503, Teollisuuskatu 3, kolikkomaksu")
    assert item["name"] == "Pysäköintilippuautomaatti 503"
    assert item["extras"]["payment:coins"] == "yes"


def test_machine_name_quoted_identifier():
    # Unit 74993: quoted identifiers carry spaces, matched whole.
    item = named(make_spider(), 'Pysäköintilippuautomaatti "Koivukylä 1", Koivukylän puistotie 5')
    assert item["name"] == 'Pysäköintilippuautomaatti "Koivukylä 1"'
    assert item["extras"]["official_name"] == 'Pysäköintilippuautomaatti "Koivukylä 1", Koivukylän puistotie 5'


def test_org_suffix_stripped_when_remainder_is_venue():
    # Unit 76970 shape (helper-level: the record is NOT_DISPLAYED).
    item = named(
        make_spider(), "Iltapäivätoiminta / Puotilan ala-aste, Marjaniemen toimintapaikka, Helsingin Jalkapalloklubi ry"
    )
    assert item["name"] == "Iltapäivätoiminta / Puotilan ala-aste, Marjaniemen toimintapaikka"


def test_bare_organisation_name_stays_whole():
    # Unit 77092 (helper-level: excluded node + no coords on the record).
    item = named(make_spider(), "Allergia-, Iho- ja Astmaliitto ry")
    assert item["name"] == "Allergia-, Iho- ja Astmaliitto ry"
    assert "official_name" not in item["extras"]


def test_closure_notes_stripped_but_kept_official():
    # Unit 59456, both casings (the pattern is case-insensitive).
    for note in ("SULJETTU TOISTAISEKSI", "suljettu toistaiseksi"):
        item = named(make_spider(), f"Kauppatori, Vironallas, {note}")
        assert item["name"] == "Kauppatori, Vironallas", note
        assert item["extras"]["official_name"].endswith(note), note


def test_announced_closure_moves_to_end_date():
    # Unit 20244.
    spider = make_spider()
    item = named(spider, "Musiikki- ja Liikuntapäiväkoti Valssi, toiminta päättyy 30.6.2026")
    assert item["name"] == "Musiikki- ja Liikuntapäiväkoti Valssi"
    spider._apply_end_date(item, {"name": {"fi": "Musiikki- ja Liikuntapäiväkoti Valssi, toiminta päättyy 30.6.2026"}})
    assert item["extras"]["end_date"] == "2026-06-30"


def test_parenthetical_school_slash_pitch():
    # Unit 78725.
    item = named(make_spider(), "Laajasalon peruskoulu (ala-aste) / Minikoripallokenttä 2")
    assert item["name"] == "Minikoripallokenttä 2"
    assert item["located_in"] == "Laajasalon peruskoulu (ala-aste)"


def test_eskola_surname_never_treated_as_venue():
    # SYNTHETIC surname guard (no Eskola venue in feed).
    item = named(make_spider(), "Palvelu, Eskola")
    assert item["name"] == "Palvelu, Eskola"
    assert "located_in" not in item


def test_swedish_water_post_translation_collapses():
    # Vesiposti, Ylästöntie 71 is unit 64782; the sv translation is constructed.
    item = named(make_spider(), "Vesiposti, Ylästöntie 71", sv="Vattenpost, Ylästöntie 71")
    assert item["name"] == "Vesiposti"
    assert item["extras"]["name:sv"] == "Vattenpost"


# ---- Quadrant B: address parsing -------------------------------------------


def test_staircase_unit():
    # Unit 80947: Leinikkitie 22 C.
    item = addressed(make_spider(), "Leinikkitie 22 C")
    assert item["street"] == "Leinikkitie"
    assert item["housenumber"] == "22"
    assert item["unit"] == "C"


def test_attached_letter_is_whole_housenumber():
    # SYNTHETIC (no feed occurrence): Katutie 2a never splits.
    item = addressed(make_spider(), "Katutie 2a")
    assert item["street"] == "Katutie"
    assert item["housenumber"] == "2a"
    assert "unit" not in item


def test_double_staircase():
    # Unit 68880: Lummetie 2 B C.
    item = addressed(make_spider(), "Lummetie 2 B C")
    assert item["housenumber"] == "2"
    assert item["unit"] == "B-C"


def test_apartment_before_stair():
    # Unit 70641: Pursimiehenkatu 8 52 A. The house is the first number.
    item = addressed(make_spider(), "Pursimiehenkatu 8 52 A")
    assert item["street"] == "Pursimiehenkatu"
    assert item["housenumber"] == "8"
    assert item["unit"] == "52 A"


def test_bare_spaced_letter_folds():
    # SYNTHETIC (no 3-token lowercase shape in feed): "Katu 5 a" is
    # housenumber 5a, never staircase a.
    item = addressed(make_spider(), "Katu 5 a")
    assert item["housenumber"] == "5a"
    assert "unit" not in item


def test_fused_staircase_apartment():
    # Unit 40930: Arabianpolku 1A2.
    item = addressed(make_spider(), "Arabianpolku 1A2")
    assert item["housenumber"] == "1A"
    assert item["unit"] == "2"


def test_stair_plus_apartment_number():
    # Unit 80834: Kiitoradantie 7 E 210.
    item = addressed(make_spider(), "Kiitoradantie 7 E 210")
    assert item["housenumber"] == "7"
    assert item["unit"] == "E 210"


def test_room_suffix():
    # Unit 68754: Työpajankatu 2 R1.
    item = addressed(make_spider(), "Työpajankatu 2 R1")
    assert item["housenumber"] == "2"
    assert item["unit"] == "R1"


def test_door_suffix_with_floor_tail():
    # Unit 78252: Sairaalatie 8, A-ovi, 2. krs.
    item = addressed(make_spider(), "Sairaalatie 8, A-ovi, 2. krs")
    assert item["housenumber"] == "8"
    assert item["unit"] == "A-ovi"


def test_staircase_word_tail():
    # Lummetie 2b, A-rappu shape (cf. unit 80680).
    item = addressed(make_spider(), "Lummetie 2b, A-rappu")
    assert item["housenumber"] == "2b"
    assert item["unit"] == "A-rappu"


def test_spaced_housenumber_range():
    # Unit 73280: Nummentie 12 - 14.
    item = addressed(make_spider(), "Nummentie 12 - 14")
    assert item["housenumber"] == "12-14"
    assert item["street"] == "Nummentie"


def test_attached_housenumber_range():
    # Unit 80709: Kunnarlantie 33-39.
    item = addressed(make_spider(), "Kunnarlantie 33-39")
    assert item["housenumber"] == "33-39"


def test_parenthetical_floor_stripped():
    # Unit 80776: Jakomäenpolku 5 (2. krs).
    item = addressed(make_spider(), "Jakomäenpolku 5 (2. krs)")
    assert item["housenumber"] == "5"
    assert "unit" not in item


def test_parenthetical_building_stripped():
    # Unit 80440: Peltokyläntie 4-6 (H-rakennus).
    item = addressed(make_spider(), "Peltokyläntie 4-6 (H-rakennus)")
    assert item["housenumber"] == "4-6"


def test_comma_floor_stripped():
    # Unit 80918: Kielotie 7 A, 2.kerros.
    item = addressed(make_spider(), "Kielotie 7 A, 2.kerros")
    assert item["housenumber"] == "7"
    assert item["unit"] == "A"


def test_comma_building_stripped():
    # Unit 79362 shape: Erätie 3, rakennus B.
    item = addressed(make_spider(), "Erätie 3, rakennus B")
    assert item["housenumber"] == "3"
    assert "unit" not in item


def test_vastapaata_stripped_case_insensitive():
    # Unit 52403.
    item = addressed(make_spider(), "Itämerenkatu 20 vastapäätä")
    assert item["housenumber"] == "20"
    assert item["street"] == "Itämerenkatu"


def test_dash_cross_streets_fall_back_to_street():
    # Unit 72684: Vaskipellontie - Lyhtytie. An intersection names no
    # single street, so the text is kept freeform instead of addr:street.
    item = addressed(make_spider(), "Vaskipellontie - Lyhtytie")
    assert item["street_address"] == "Vaskipellontie - Lyhtytie"
    assert "street" not in item


def test_comma_visiting_address_wins():
    # Keskustakirjasto Oodi shape (cf. unit 60729).
    item = addressed(make_spider(), "Keskustakirjasto Oodi, Töölönlahdenkatu 4")
    assert item["street"] == "Töölönlahdenkatu"
    assert item["housenumber"] == "4"


def test_comma_district_loses_to_numbered_head():
    # Unit 57307: Mikkolankuja 1, Oulunkylä.
    item = addressed(make_spider(), "Mikkolankuja 1, Oulunkylä")
    assert item["street"] == "Mikkolankuja"
    assert item["housenumber"] == "1"


def test_kayntiosoite_prefix_wins():
    # Unit 64482: Itäkatu 11, käyntiosoite: Tallinnanaukio 1.
    item = addressed(make_spider(), "Itäkatu 11, käyntiosoite: Tallinnanaukio 1")
    assert item["street"] == "Tallinnanaukio"
    assert item["housenumber"] == "1"


def test_trailing_district_words_stripped():
    # SYNTHETIC (double-district shape): Ratakatu 6 Kaartinkaupunki Helsinki.
    item = addressed(make_spider(), "Ratakatu 6 Kaartinkaupunki Helsinki")
    assert item["street"] == "Ratakatu"
    assert item["housenumber"] == "6"


def test_single_token_street_vs_place():
    # Unit 80758: Nupurinjärvenpolku.
    item = addressed(make_spider(), "Nupurinjärvenpolku")
    assert item["street"] == "Nupurinjärvenpolku"
    # Unit 80786: Villinki.
    item = addressed(make_spider(), "Villinki")
    assert item["extras"]["addr:place"] == "Villinki"


def test_bare_street_without_number():
    # Urho Kekkosen katu street (cf. unit 80691 address).
    item = addressed(make_spider(), "Urho Kekkosen katu")
    assert item["street"] == "Urho Kekkosen katu"


def test_swedish_street_with_number():
    # Unit 79632: Västankvarnsvägen 399.
    item = addressed(make_spider(), "Västankvarnsvägen 399")
    assert item["housenumber"] == "399"


def test_venue_word_address_without_located_in_falls_back():
    # Unit 75107: Sanomalan paviljonkikoulu. Venue-looking addresses stay
    # freeform street_address; located_in is reserved for name splits.
    item = addressed(make_spider(), "Sanomalan paviljonkikoulu")
    assert item["street_address"] == "Sanomalan paviljonkikoulu"
    assert "located_in" not in item


def test_place_suffix_takes_addr_place():
    # Unit 64719 address shape (Iso Vasikkasaari).
    item = addressed(make_spider(), "Iso Vasikkasaari")
    assert item["extras"]["addr:place"] == "Iso Vasikkasaari"


def test_numberless_place_pair():
    # Iso Mustasaari addresses (cf. unit 60003).
    item = addressed(make_spider(), "Iso Mustasaari, Suomenlinna")
    assert item["extras"]["addr:place"] == "Iso Mustasaari, Suomenlinna"


def test_dash_sentinels_yield_no_address():
    # Unit 80738 shape ("-") and its en-dash twin: sentinels, not streets.
    for raw in ("-", "\u2013"):
        item = addressed(make_spider(), raw)
        assert "street" not in item, raw
        assert "housenumber" not in item, raw


# ---- Quadrant C: category mapping ------------------------------------------


def test_school_nurse_colocation_resolves_nurse():
    # Unit 78288.
    item = full(make_spider(), "Suutarilan peruskoulu, kouluterveydenhuolto", [2165, 2164])
    assert item.get_tag("healthcare") == "nurse"


def test_plain_clinic():
    # Unit 80698: CLINIC carries amenity=clinic (nurse-led units carry healthcare=nurse instead).
    item = full(make_spider(), "Lähilääkärit Leppävaara -palvelupiste", [991])
    assert item.get_tag("amenity") == "clinic"


def test_hotel_beats_nature_reserve_filing():
    # Unit 62682.
    item = full(make_spider(), "Hotelli Nuuksio", [736, 708, 151, 260, 507, 742, 751])
    assert item.get_tag("tourism") == "hotel"


def test_community_beats_gym():
    # Unit 42653: COMMUNITY_CENTRE carries amenity=community_centre.
    item = full(make_spider(), "Havukosken nuorisotilan kuntosali", [611, 366, 263, 510, 154])
    assert item.get_tag("amenity") == "community_centre"


def test_parking_bottom():
    # Unit 75358.
    item = full(make_spider(), "Marketparkki", [531, 533])
    assert item.get_tag("amenity") == "parking"


def test_metro_letter_suffix_is_entrance():
    # Unit 58006.
    item = full(make_spider(), "Vuosaaren metroasema C", [519])
    assert item.get_tag("railway") == "subway_entrance"
    assert item.get_tag("station") is None


def test_bare_railway_station_stays_station():
    # Unit 44740: Kivistön asema.
    item = full(make_spider(), "Kivistön asema", [520])
    assert item.get_tag("railway") == "station"


def test_swim_hall_tail_beats_gym_filing():
    # Unit 42884.
    item = full(make_spider(), "Hakunilan uimahalli", [611, 2226, 693])
    assert item.get_tag("leisure") == "sports_centre"
    assert item.get_tag("sport") == "swimming"


def test_reverse_ordered_gym_annex_stays_gym():
    # SYNTHETIC: "Kuntosali / Hakunilan uimahalli".
    item = full(make_spider(), "Kuntosali / Hakunilan uimahalli", [611, 693])
    assert item.get_tag("leisure") == "fitness_centre"


def test_gym_only_annex_without_tail_stays_gym():
    # Unit 79527 shape: Siuntion uimahallin kuntosali.
    item = full(make_spider(), "Siuntion uimahallin kuntosali", [611])
    assert item.get_tag("leisure") == "fitness_centre"


def test_laboratory_name_beats_filing():
    # Unit 77647.
    item = full(make_spider(), "Espoonlahden laboratorio", [1017, 1010])
    assert item.get_tag("healthcare") == "laboratory"


def test_university_lab_beats_medical_lab():
    # SYNTHETIC: university lab is research, not a medical lab.
    item = full(make_spider(), "Kielilaboratorio", [1359])
    assert item.get_tag("office") == "research"


def test_university_buildings_map_as_nodes():
    # Units 76785 (Biokeskus 1), 75353 (Päärakennus): individual buildings
    # map building=university on the node; the institution tag stays off.
    item = full(make_spider(), "Biokeskus 1", [1359])
    assert item.get_tag("building") == "university"
    assert item.get_tag("amenity") is None
    item = full(make_spider(), "Helsingin yliopiston päärakennus", [1359])
    assert item.get_tag("building") == "university"


def test_youth_guidance_is_office():
    # Unit 53329.
    item = full(make_spider(), "Nuorten urapalvelut", [2156, 490])
    assert item.get_tag("office") == "government"


def test_espoo_info_desk():
    # Unit 53543.
    item = full(make_spider(), "Espoonlahden Espoo-info", [319, 316, 744, 341])
    assert item.get_tag("tourism") == "information"
    assert item["extras"]["information"] == "office"


def test_vantaa_info_desk_untabled():
    # Unit 72611: HSL, Vantaa-info Tikkurila.
    item = full(make_spider(), "HSL, Vantaa-info Tikkurila", [514])
    assert item.get_tag("tourism") == "information"
    assert item["extras"]["information"] == "office"


def test_helsinki_info_desk():
    # Unit 73317.
    item = full(make_spider(), "Stoa Helsinki-info", [319, 189, 857])
    assert item.get_tag("tourism") == "information"


def test_employment_info_stays_office():
    # Unit 78729: Helsinki-info, Työllisyyspalvelut Kamppi.
    item = full(make_spider(), "Helsinki-info, Työllisyyspalvelut Kamppi", [319, 189, 857])
    assert item.get_tag("office") == "government"


def test_tourist_information_subtag():
    # Unit 69016: staffed tourist info takes the documented office value.
    item = full(make_spider(), "Helsingin matkailuneuvonta", [319, 144, 316, 744, 748])
    assert item.get_tag("tourism") == "information"
    assert item["extras"]["information"] == "office"


def test_signboard_is_board_not_office():
    # Unit 68525 shape: Opastetaulu, Ehrenströmintie.
    item = full(make_spider(), "Opastetaulu, Ehrenströmintie", [2365])
    assert item.get_tag("tourism") == "information"
    assert item["extras"]["information"] == "board"


def test_bar_beats_cafe_by_name():
    # Units 72902 (Bär Bar Tripla) and 71834 (Little Big Cafe BAR).
    for fi, nodes in (("Bär Bar Tripla", [738]), ("Little Big Cafe BAR", [738, 751])):
        item = full(make_spider(), fi, nodes)
        assert item.get_tag("amenity") == "bar", fi


def test_bakery_refine_beats_cafe_filing():
    # Unit 79751.
    item = full(make_spider(), "Mytäjäisten kotileipomo", [738])
    assert item.get_tag("shop") == "bakery"


def test_bakery_rescue_untabled():
    # SYNTHETIC: Leipomo Cakemaster shape, routed through the full path so
    # the missing-branch dispatch is pinned too.
    item = full(make_spider(), "Leipomo Cakemaster", [99999])
    assert item.get_tag("shop") == "bakery"


def test_mall_beats_events_filing():
    # Unit 78774.
    item = full(make_spider(), "Iso Omena", [750, 2173])
    assert item.get_tag("shop") == "mall"


def test_mall_suffix_without_comma():
    # Unit 60250: Myllypuron Ostari.
    item = full(make_spider(), "Myllypuron Ostari", [750])
    assert item.get_tag("shop") == "mall"


def test_mall_tenant_does_not_inherit_mall():
    # Unit 77525: Kaisan Cafe Iso Omena.
    item = full(make_spider(), "Kaisan Cafe Iso Omena", [738])
    assert item.get_tag("amenity") == "cafe"
    assert item.get_tag("shop") is None


def test_jokamiesgolf_is_full_course():
    # Unit 68855.
    item = full(make_spider(), "Paloheinä Golf / Evergreen / Jokamiesgolfkenttä", [637])
    assert item.get_tag("leisure") == "golf_course"


def test_par3_is_full_course():
    # Unit 79583.
    item = full(make_spider(), "Pickala Golf Garden Par3", [635])
    assert item.get_tag("leisure") == "golf_course"


def test_seikkailugolf_is_miniature():
    # Unit 72448.
    item = full(make_spider(), "Seikkailugolf Oittaa", [637])
    assert item.get_tag("leisure") == "miniature_golf"


def test_minigolf_bar_is_miniature():
    # Unit 75540.
    item = full(make_spider(), "Helsinki Camping - Minigolf Bar & Nightclub", [2246, 2174])
    assert item.get_tag("leisure") == "miniature_golf"


def test_ride_tracks_are_tracks_with_cycling():
    # Units 78583 (Pumptrack) and 57289 (BMX-rata): ride tracks, not pitches.
    for fi in ("Malmin kenttä / Väliaikainen Pumptrack", "Matinkylän urheilupuiston BMX-rata"):
        item = full(make_spider(), fi, [650])
        assert item.get_tag("leisure") == "track", fi
        assert item.get_tag("sport") == "cycling", fi


def test_salibandy_rink_is_floorball():
    # Unit 78571.
    item = full(make_spider(), "Oulunkylän liikuntapuisto / Salibandykaukalo", [641, 661])
    assert item.get_tag("leisure") == "pitch"
    assert item.get_tag("sport") == "floorball"


def test_hiekkaharju_district_gives_no_surface():
    # Unit 42448: Hiekkaharjun koulun koripallokenttä (657 resolves to 654).
    item = full(make_spider({657: 654}), "Hiekkaharjun koulun koripallokenttä", [657])
    assert item.get_tag("sport") == "basketball"
    assert "surface" not in item["extras"]


def test_sand_pitch_surface_control():
    # Control: a real sand pitch names the surface ("Hiekkakenttä" ×371).
    # SYNTHETIC bare sand name (no exact feed name).
    item = full(make_spider(), "Hiekkakenttä", [654])
    assert item["extras"]["surface"] == "sand"


def test_american_football_abbreviation():
    # Unit 41918: Käpylän liikuntapuisto / Amer. jalkapallokenttä (659 resolves to 654).
    item = full(make_spider({659: 654}), "Käpylän liikuntapuisto / Amer. jalkapallokenttä", [659])
    assert item.get_tag("sport") == "american_football"


def test_beachfutis_is_soccer():
    # Unit 57336: Oittaan beachfutiskenttä (659 resolves to 654).
    item = full(make_spider({659: 654}), "Oittaan beachfutiskenttä", [659])
    assert item.get_tag("sport") == "soccer"


def test_playground_access_customers_only():
    # Leo's Leikkimaa Tripla is unit 63874; the yard names are constructed.
    spider = make_spider()
    item = Feature()
    spider._apply_subtags(item, {"name": {"fi": "Leo's Leikkimaa Tripla"}}, Categories.LEISURE_PLAYGROUND)
    assert item["extras"]["access"] == "customers"
    # Yard restrictions are not feed-verifiable: no access tag either way.
    for fi in ("Lintumetsän koulu lähiliikuntapaikka", "Päiväkoti Piilometsän leikkipiha"):
        item = Feature()
        spider._apply_subtags(item, {"name": {"fi": fi}}, Categories.LEISURE_PLAYGROUND)
        assert "access" not in item["extras"], fi


def test_public_playground_full_path():
    # Unit 80964: "Leikkipuisto Lehdokki, leikkipiha" filed under daycare
    # nodes, but the city runs leikkipuistot open and free with no placement
    # (hel.fi: Playgrounds), so playground beats the daycare filing.
    spider = make_spider({976: 975, 975: 868})
    item = full(spider, "Leikkipuisto Lehdokki, leikkipiha", [976])
    assert item.get_tag("leisure") == "playground"


def test_daycare_worded_playground_stays_kindergarten():
    # SYNTHETIC guard: a real daycare at a playground keeps kindergarten.
    spider = make_spider({976: 975, 975: 868})
    item = full(spider, "Päiväkoti Leikkipuisto", [976])
    assert item.get_tag("amenity") == "kindergarten"


def test_laavu_is_shelter():
    # Unit 80761.
    item = full(make_spider(), "Laavu", [697])
    assert item.get_tag("amenity") == "shelter"


def test_civil_defence_shelter_is_bomb_shelter():
    # Units 68539/68494 (nodes 1086/1084 inherit from 1083): civilian
    # shelters tag amenity=shelter + shelter_type=bomb_shelter, never
    # military=bunker.
    item = categorised(make_spider({1086: 1083}), "Koivusaaren metroaseman yleinen väestönsuoja", [1086])
    assert item.get_tag("amenity") == "shelter"
    assert item["extras"]["shelter_type"] == "bomb_shelter"
    assert item.get_tag("military") is None


def test_memorial_named_artwork_is_memorial():
    # Unit 55958: national Winter War memorial filed as public art.
    item = full(make_spider(), "Talvisodan kansallinen muistomerkki", [2006])
    assert item.get_tag("historic") == "memorial"
    assert item.get_tag("tourism") is None
    # memorial=* subtypes by noun (units 23494, 23142).
    item = full(make_spider(), "Tove Janssonin muistolaatta", [2006])
    assert item["extras"]["memorial"] == "plaque"
    item = full(make_spider(), "Marsalkka Mannerheimin ratsastajapatsas", [2006])
    assert item["extras"]["memorial"] == "statue"


def test_talkoolaituri_is_tool_library():  # Unit 79897: Clean-up station, not a pier.
    item = full(make_spider(), "Kaupunginpuutarhan talkoolaituri", [2235, 72])
    assert item.get_tag("amenity") == "tool_library"


def test_galltrask_single_node_falls_back_to_park():
    # Unit 69090.
    item = full(make_spider(), "Gallträskin virkistysalue", [711])
    assert item.get_tag("leisure") == "park"


def test_visitor_centre_keeps_attraction_despite_711():
    # Unit 57691.
    item = full(make_spider(), "Suomenlinnan vierailijakeskus", [316, 744, 711, 749, 145])
    assert item.get_tag("tourism") == "attraction"


def test_sports_centre_keeps_events_despite_711():
    # Unit 21208: Tapanilan Urheilukeskus.
    item = full(make_spider(), "Tapanilan Urheilukeskus", [151, 260, 507, 742, 711])
    assert item.get_tag("amenity") == "events_venue"


def test_church_filed_as_sight_stays_church():
    # Unit 78782 shape: Seutulan kappeli.
    item = full(make_spider(), "Seutulan kappeli", [350, 749])
    assert item.get_tag("amenity") == "place_of_worship"


def test_church_tower_has_no_premises():
    # Unit 77517 shape: Kallion kirkon torni. A tower is not a visitable
    # church, so no worship tag — but the guided tower visits (273 steps,
    # city views) make it a sight, not a generic record.
    item = full(make_spider(), "Kallion kirkon torni", [350, 749])
    assert item.get_tag("tourism") == "attraction"
    assert item["name"] == "Kallion kirkon torni"


def test_boat_berths_stay_uncategorised():
    # Unit 59456: no honest tag, so amenity=yes (generic), never tagless.
    item = full(make_spider(), "Kauppatori, Vironallas", [2198, 2199])
    assert item.get_tag("amenity") == "yes"


def test_company_hq_beats_recycling_filing():
    # Unit 9392.
    item = full(
        make_spider(),
        "Pääkaupunkiseudun Kierrätyskeskus Oy, Hallinto ja Ympäristökoulu",
        [52],
    )
    assert item.get_tag("office") == "company"


def test_manege_carries_equestrian():
    # Unit 79662.
    item = full(make_spider(), "Stall Råbackan maneesi", [556])
    assert item.get_tag("sport") == "equestrian"


def test_group_home_for_disabled():
    # Unit 79151.
    item = full(make_spider(), "Pikkukosken ryhmäkoti", [803, 2442])
    assert item.get_tag("social_facility") == "group_home"
    assert item["extras"]["social_facility:for"] == "disabled"


def test_mental_health_housing_overrides_senior():
    # SYNTHETIC: nursing home co-filed with mental-health housing.
    item = full(make_spider(), "Kompassi", [825, 2160])
    assert item.get_tag("social_facility") == "group_home"
    assert item["extras"]["social_facility:for"] == "mental_health"


def test_maternal_clinic_speciality():
    # Unit 78248 shape: CLINIC carries amenity=clinic plus the speciality.
    item = full(make_spider(), "Siuntion sydän -perhekeskus, neuvola", [1005, 1004, 1006, 1008])
    assert item.get_tag("amenity") == "clinic"
    assert item["extras"]["healthcare:speciality"] == "maternal_and_child_health"


def test_addiction_clinic_speciality():
    # SYNTHETIC bare service name on the Korvaushoito node.
    item = full(make_spider(), "Korvaushoito", [1055])
    assert item["extras"]["healthcare:speciality"] == "addiction"


def test_double_food_noun_takes_first_table_match():
    # Unit 78911: "Kahvila-ravintola Håkans" heads with Kahvila, and the
    # single NOUN_TABLE serves both paths in one order (kahvila < ravintola).
    item = full(make_spider(), "Kahvila-ravintola Håkans", [738, 751])
    assert item.get_tag("amenity") == "cafe"


def test_school_nurse_speciality():
    # SYNTHETIC bare service names for the speciality split.
    # Kouluterveydenhuolto is preventive/paediatric; opiskeluterveydenhuolto
    # serves older students, so community alone.
    item = full(make_spider(), "Kouluterveydenhoito", [2164])
    assert item.get_tag("healthcare") == "nurse"
    assert item["extras"]["healthcare:speciality"] == "community;paediatrics"
    item = full(make_spider(), "Opiskeluterveydenhuolto", [2166])
    assert item["extras"]["healthcare:speciality"] == "community"


def test_loading_dock_filed_as_ticket_gets_dock_tag():
    # Unit 59265: A Bloc lastauslaituri is a service-yard dock, not ticket sales.
    item = full(make_spider(), "A Bloc lastauslaituri", [514])
    assert item.get_tag("shop") is None
    assert item.get_tag("amenity") == "loading_dock"


def test_ticket_service_point_is_ticket_shop():
    # Units 72600-72602: HSL Asiointipiste service points sell tickets.
    item = full(make_spider(), "HSL Asiointipiste Kalajärvi", [514])
    assert item.get_tag("shop") == "ticket"


def test_lipas_extras_surface_lighting_toilets():
    # SYNTHETIC constructed unit id 999010 with LIPAS extras.
    # LIPAS facility data beats name inference; closed vocabularies only.
    spider = make_spider()
    item = spider._build_item(
        {
            "id": 999010,
            "name": {"fi": "Hiekkakenttä"},
            "service_nodes": [659],
            "location": {"coordinates": [24.9, 60.1]},
            "extra": {
                "lipas.surfaceMaterial": "Kivituhka",
                "lipas.ligthing": "1",
                "lipas.toilet": "1",
            },
        }
    )
    assert item["extras"]["surface"] == "fine_gravel"
    assert item["extras"]["lit"] == "yes"
    assert item["extras"]["toilets"] == "yes"


def test_lipas_correct_lighting_spelling_accepted():
    # SYNTHETIC constructed unit id 999012 (feed spells it "ligthing"):
    # a feed fix to the correct spelling must keep working.
    spider = make_spider()
    item = spider._build_item(
        {
            "id": 999012,
            "name": {"fi": "Kenttä"},
            "service_nodes": [659],
            "location": {"coordinates": [24.9, 60.1]},
            "extra": {"lipas.lighting": "1"},
        }
    )
    assert item["extras"]["lit"] == "yes"


def test_picture_url_becomes_image():
    # SYNTHETIC constructed unit id 999011.
    spider = make_spider()
    item = spider._build_item(
        {
            "id": 999011,
            "name": {"fi": "Kenttä"},
            "service_nodes": [659],
            "location": {"coordinates": [24.9, 60.1]},
            "picture_url": "https://api.hel.fi/servicemap/v2/unit/999011/picture/",
        }
    )
    assert item["image"] == "https://api.hel.fi/servicemap/v2/unit/999011/picture/"


def test_new_pitch_and_facility_rows():
    # Nodes 659/658/661/656 (ball/volley/roller/football), 613 (weights),
    # 627 (table-tennis rooms mirror outdoor 2356), 1040 (foot therapy),
    # 2268 (rentals), 514 (ticket points). Bare node names constructed;
    # Puistokenttä Autioniitty is Unit 57415.
    assert full(make_spider(), "Pallokenttä", [659]).get_tag("leisure") == "pitch"
    item = full(make_spider(), "Puistokenttä Autioniitty", [658])
    assert item.get_tag("leisure") == "pitch"
    assert item.get_tag("sport") == "volleyball"
    assert full(make_spider(), "Rullakiekkokenttä", [661]).get_tag("leisure") == "pitch"
    assert full(make_spider(), "Voimailusali", [613]).get_tag("leisure") == "fitness_station"
    item = full(make_spider(), "Pöytätennistila", [627])
    assert item.get_tag("sport") == "table_tennis"
    assert full(make_spider(), "Jalkaterapia", [1040]).get_tag("healthcare") == "podiatrist"
    assert full(make_spider(), "Vuokrauspalvelu", [2268]).get_tag("shop") == "rental"


def test_third_wave_table_rows():
    # Nodes 2298/2297 (phone/computer repair join the 2299/2300 craft
    # group), 574 (outdoor climbing areas), 670 (kart tracks),
    # 678 (whitewater canoe centres). Units 64280/64278 repair,
    # 78891 climbing, 79339 karting, 79681 canoe centre.
    assert full(make_spider(), "Oy Wega-product Ab", [2298]).get_tag("craft") == "electronics_repair"
    assert full(make_spider(), "Mikrotukikohta", [2297]).get_tag("craft") == "electronics_repair"
    # Retail names stay out of the repair filing even on the new rows.
    assert full(make_spider(), "Digishop Arabia", [2303, 2298, 2297]).get_tag("craft") is None
    # Earlier second-hand filing beats the repair rows (Fonum, Grenius).
    assert full(make_spider(), "Fonum Kamppi", [2249, 2298]).get_tag("shop") == "second_hand"
    item = full(make_spider(), "Kiipeilyalue", [574])
    assert item.get_tag("leisure") == "pitch"
    assert item.get_tag("sport") == "climbing"
    item = full(make_spider(), "VM Karting Center", [2246, 670])
    assert item.get_tag("leisure") == "track"
    assert item.get_tag("sport") == "karting"
    assert full(make_spider(), "Siuntion Melontakeskus", [678]).get_tag("leisure") == "sports_centre"


def test_heterogeneous_workshop_node_stays_generic():
    # Node 389 mixes bike workshops, motor halls and training areas: no
    # single shop tag is honest (cf. units 8076, 8034).
    assert full(make_spider(), "Moottorihalli", [389]).get_tag("shop") is None


def test_second_wave_table_rows():
    # Clinical splits, nurse point, daycare/preschool splits, academic libraries.
    assert full(make_spider(), "Päivystys", [1001]).get_tag("amenity") == "clinic"
    assert full(make_spider(), "Sairaala", [1012]).get_tag("amenity") == "hospital"
    assert full(make_spider(), "Vastaanotto", [992]).get_tag("amenity") == "clinic"
    item = full(make_spider(), "Neuvola", [1008])
    assert item.get_tag("amenity") == "clinic"
    assert item["extras"]["healthcare:speciality"] == "maternal_and_child_health"
    assert full(make_spider(), "Rokotuspiste", [993]).get_tag("healthcare") == "nurse"
    assert full(make_spider(), "Päivähoito", [871]).get_tag("amenity") == "kindergarten"
    assert full(make_spider(), "Esiopetus", [2125]).get_tag("amenity") == "kindergarten"
    assert full(make_spider(), "Kirjasto", [2197]).get_tag("amenity") == "library"
    # Pitch sports, halls, golf.
    assert full(make_spider(), "Koripallokenttä", [657]).get_tag("sport") == "basketball"
    assert full(make_spider(), "Beachvolley", [655]).get_tag("sport") == "beachvolleyball"
    assert full(make_spider(), "Padel", [2355]).get_tag("sport") == "padel"
    assert full(make_spider(), "Pesäpallostadion", [660]).get_tag("sport") == "baseball"
    item = full(make_spider(), "Tennishalli", [623])
    assert item.get_tag("leisure") == "sports_hall"
    assert item.get_tag("sport") == "tennis"
    assert full(make_spider(), "Keilahalli", [607]).get_tag("leisure") == "bowling_alley"
    assert full(make_spider(), "Golfkenttä", [637]).get_tag("leisure") == "golf_course"
    assert full(make_spider(), "Seikkailugolf Oittaa", [637]).get_tag("leisure") == "miniature_golf"
    assert full(make_spider(), "Parkoursali", [626]).get_tag("sport") == "parkour"
    assert full(make_spider(), "Skeittihalli", [620]).get_tag("sport") == "skateboard"
    assert full(make_spider(), "Liikuntahalli", [616]).get_tag("leisure") == "sports_hall"
    assert full(make_spider(), "Areena", [617]).get_tag("leisure") == "sports_centre"
    assert full(make_spider(), "Kiipeilyseinä", [629]).get_tag("leisure") == "sports_centre"
    assert full(make_spider(), "Pyöräilyalue", [650]).get_tag("leisure") == "track"
    # Shops, repair, offices, special POIs.
    assert full(make_spider(), "Vuokraus", [2267]).get_tag("shop") == "rental"
    assert full(make_spider(), "Vaatelainaamo", [2266]).get_tag("shop") == "rental"
    assert full(make_spider(), "Kiertotalous", [2305]).get_tag("shop") == "second_hand"
    assert full(make_spider(), "Kauppa", [727]).get_tag("shop") == "gift"
    assert full(make_spider(), "Posti", [176]).get_tag("amenity") == "post_office"
    assert full(make_spider(), "Korjaus", [2300]).get_tag("craft") == "electronics_repair"
    assert full(make_spider(), "Kellokorjaamo", [2302]).get_tag("craft") == "watchmaker"
    assert full(make_spider(), "Toimisto", [2005]).get_tag("office") == "government"
    assert full(make_spider(), "Lainhuuto", [244]).get_tag("office") == "government"
    assert full(make_spider(), "Arkisto", [309]).get_tag("amenity") == "archive"
    assert full(make_spider(), "Perhekuntoutus", [2334]).get_tag("amenity") == "social_facility"
    assert full(make_spider(), "Maahanmuuttajapalvelut", [189]).get_tag("office") == "government"
    assert full(make_spider(), "Musiikkikoulu", [2409]).get_tag("amenity") == "music_school"
    assert full(make_spider(), "Vainajatila", [2446]).get_tag("amenity") == "mortuary"
    # Rescue-school names read as schools per the koulu convention, but the
    # explicit row still rescues the unit from generic (cf. unit 8966).
    assert full(make_spider(), "Pelastuskoulu", [1073]).get_tag("amenity") == "school"
    assert full(make_spider(), "Leikkipaikka", [501]).get_tag("leisure") == "playground"
    assert full(make_spider(), "Ulkokuntoilupaikka", [2440]).get_tag("leisure") == "fitness_station"


def test_specific_cofiling_beats_generic_venue():
    # Unit 78853: church co-filed as events venue stays a church.
    item = full(make_spider(), "Myyrmäen kirkko", [350, 2173])
    assert item.get_tag("amenity") == "place_of_worship"
    # Library / office buildings filed as sights keep their facility.
    # Single-node misfilings (cf. Vallilan kirjasto, unit 80323) resolve via
    # the kirjasto nouns in NOUN_TABLE; co-tagged units via the rule below.
    item = full(make_spider(), "Vallilan kirjasto", [749])
    assert item.get_tag("amenity") == "library"
    item = full(make_spider(), "Sähkötalon asiakaspalvelu", [749, 2203])
    assert item.get_tag("office") == "government"
    item = full(make_spider(), "Ympäristökeskus", [57, 2203])
    assert item.get_tag("office") == "government"
    # A venue without sauna words is not a sauna (cf. Teurastamo).
    item = full(make_spider(), "Teurastamo", [155, 2173])
    assert item.get_tag("amenity") == "events_venue"
    # Advice desks on retail units follow the shop (cf. Taito Shop 76939).
    item = full(make_spider(), "Taito Shop", [2187, 711])
    assert item.get_tag("shop") == "yes"
    # Advice offices are not kindergartens (cf. unit 54059).
    item = full(make_spider(), "Palveluneuvonta", [868, 2004])
    assert item.get_tag("office") == "government"


def test_hired_venue_at_library_keeps_program():
    # Units 80660/80655: peer-support programs hired at the library are not
    # libraries; the hired-venue rule outranks the kirjasto noun.
    item = full(make_spider(), "Aivotreenit - Vuosaaren kirjasto -palvelun järjestämispaikka", [1021, 768])
    assert item.get_tag("amenity") == "community_centre"
    # Parks named after libraries stay parks (cf. Kirjastonpuisto).
    item = full(make_spider(), "Kirjastonpuisto", [70, 501])
    assert item.get_tag("leisure") == "playground"


def test_wellness_studio_without_sauna_word_keeps_table():
    # Pranama Kallio (unit 78519) is a yoga studio, not a sauna: a 2168
    # filing without sauna evidence or an owned trade word is generic.
    # Rental-sauna rows (155/264/511) still yield to a co-filed events venue.
    item = full(make_spider(), "Pranama Kallio", [2168, 2173])
    assert item.get_tag("amenity") == "yes"
    # Unit 78500 is literally named "Hyvinvointitila".
    item = full(make_spider(), "Hyvinvointitila", [2168])
    assert item.get_tag("amenity") == "yes"
    item = full(make_spider(), "Teurastamo", [155, 2173])
    assert item.get_tag("amenity") == "events_venue"


def test_retail_shop_filed_as_repair_uses_name():
    # Unit 72392: camera shop filed as repair resolves by name (photo).
    item = full(make_spider(), "JAS Kamerakauppa", [2302, 2299, 2300])
    assert item.get_tag("shop") == "photo"
    # Brand-only repair names keep their filing (cf. EsaFix, unit 76956).
    item = full(make_spider(), "EsaFix Oy", [2300])
    assert item.get_tag("craft") == "electronics_repair"


def test_group_home_filed_as_office():
    # Unit 76608: family group home filed under immigrant services.
    item = full(make_spider(), "Keravan perheryhmäkoti", [857, 189])
    assert item.get_tag("amenity") == "social_facility"
    assert item["extras"]["social_facility"] == "group_home"


def test_new_rescue_nouns():
    # Bare playgrounds and allotment gardens with no tabled node; computer
    # and phone repair shops. Bare nouns on fake node 99999;
    # Oulunkylän siirtolapuutarha is unit 57194.
    assert full(make_spider(), "Leikkipaikka", [99999]).get_tag("leisure") == "playground"
    assert full(make_spider(), "Palstat", [99999]).get_tag("landuse") is None
    item = full(make_spider(), "Oulunkylän siirtolapuutarha", [99999])
    assert item.get_tag("landuse") == "allotments"
    assert full(make_spider(), "Tietokonehuolto", [99999]).get_tag("craft") == "electronics_repair"
    assert full(make_spider(), "Puhelinhuolto", [99999]).get_tag("craft") == "electronics_repair"


def test_table_extras_ride_along():
    # Same-category extras (station, vending, sport, speciality) land on output.
    # SYNTHETIC bare names isolate same-category extras.
    assert full(make_spider(), "Asema", [519]).get_tag("railway") == "station"
    assert full(make_spider(), "Automaatti", [530]).get_tag("vending") == "parking_tickets"
    assert full(make_spider(), "Kaukalo", [641]).get_tag("sport") == "ice_hockey"


def test_city_postcode_country_pins():
    # SYNTHETIC constructed unit id 999012.
    spider = make_spider()
    item = spider._build_item(
        {
            "id": 999012,
            "name": {"fi": "Kirjasto"},
            "service_nodes": [324],
            "municipality": "helsinki",
            "address_zip": " 00100 ",
            "street_address": {"fi": "Katu 1"},
            "location": {"coordinates": [24.9, 60.1]},
        }
    )
    assert item["city"] == "Helsinki"
    assert item["postcode"] == "00100"
    assert item["country"] == "FI"


def test_bare_pitch_counts_no_sport():
    # SYNTHETIC bare pitch name for the no-sport stat.
    spider = make_spider()
    item = full(spider, "Kenttä", [659])
    assert item.get_tag("leisure") == "pitch"
    assert item.get_tag("sport") is None
    assert spider.crawler.stats.get_value("atp/helsinki_servicemap_fi/category/pitch_no_sport") == 1


def test_service_ids_shapes():
    # SYNTHETIC service_nodes shapes.
    spider = make_spider()
    assert spider._service_ids({"service_nodes": "991"}) == [991]
    assert spider._service_ids({"service_nodes": 991}) == [991]
    assert spider._service_ids({"service_nodes": ["991", "junk", None]}) == [991]
    assert spider._service_ids({}) == []


def test_bad_coords_drop_no_coords():
    # SYNTHETIC constructed unit id 999013.
    spider = make_spider()
    for coords in ([24.9, 95.0], ["x", "y"], [24.9], {"lon": 24.9}):
        assert (
            spider._build_item(
                {
                    "id": 999013,
                    "name": {"fi": "Kenttä"},
                    "service_nodes": [659],
                    "location": {"coordinates": coords},
                }
            )
            is None
        )


def test_water_post_beats_billing_office():
    # Unit 75288.
    item = full(make_spider(), "Vesiposti, Kuninkaankartanontie", [301, 93])
    assert item.get_tag("amenity") == "drinking_water"


# ---- Quadrant D: operator, brand, contact, filters --------------------------


def test_private_eatery_gets_no_named_operator():
    # Unit 80931.
    _, item = operated(
        Categories.RESTAURANT,
        {"displayed_service_owner_type": "PRIVATE_SERVICE", "municipality": "helsinki"},
    )
    assert "operator" not in item
    assert item["extras"]["operator:type"] == "private"


def test_private_kindergarten_gets_type_but_no_name():
    # SYNTHETIC: private daycare with an organizer name.
    _, item = operated(
        Categories.KINDERGARTEN,
        {
            "displayed_service_owner_type": "PRIVATE_SERVICE",
            "organizer_name": "Pilke päiväkodit Oy",
            "municipality": "espoo",
        },
    )
    assert "operator" not in item
    assert item["extras"]["operator:type"] == "private"


def test_municipal_organizer_beats_department():
    # SYNTHETIC: NGO operator on a municipal record.
    _, item = operated(
        Categories.FIRE_STATION,
        {
            "organizer_name": "Haagan VPK",
            "root_department": "d1",
            "municipality": "helsinki",
        },
        {"d1": "Helsingin kaupunki"},
    )
    assert item["operator"] == "Haagan VPK"
    assert "operator_wikidata" not in item


def test_municipal_operator_with_wikidata():
    # SYNTHETIC constructed department/municipality pair.
    _, item = operated(
        Categories.THEATRE,
        {"root_department": "d1", "municipality": "helsinki"},
        {"d1": "Helsingin kaupunki"},
    )
    assert item["operator"] == "Helsingin kaupunki"
    assert item["operator_wikidata"] == "Q1757"


def test_cross_city_operator_dropped():
    # SYNTHETIC: Espoo department operating in Helsinki.
    spider, item = operated(Categories.THEATRE, {"organizer_name": "Espoon kaupunki", "municipality": "helsinki"})
    assert "operator" not in item
    assert spider.crawler.stats.get_value("atp/helsinki_servicemap_fi/operator/mismatch") == 1


def test_missing_municipality_drops_city_operator():
    # SYNTHETIC.
    spider, item = operated(Categories.THEATRE, {"organizer_name": "Espoon kaupunki", "municipality": ""})
    assert "operator" not in item
    assert spider.crawler.stats.get_value("atp/helsinki_servicemap_fi/operator/no_municipality") == 1


def test_pilke_spelling_canonicalized():
    # Unit 20369 shape: organizer "Pilkepäiväkodit Oy".
    _, item = operated(Categories.KINDERGARTEN, {"organizer_name": "Pilkepäiväkodit Oy", "municipality": "espoo"})
    assert item["operator"] == "Pilke päiväkodit Oy"


def test_ry_doubling_collapsed():
    # SYNTHETIC: feed truncation artifact.
    long_name = "Arabianrannan Montessorileikkikoulu"
    _, item = operated(
        Categories.KINDERGARTEN,
        {"organizer_name": long_name + " r " + long_name + " y", "municipality": "helsinki"},
    )
    assert item["operator"] == long_name + " ry"


def test_archaic_railway_name_normalized():
    # Unit 14469.
    _, item = operated(Categories.TRAIN_STATION, {"organizer_name": "Valtion rautatiet", "municipality": "espoo"})
    assert item["operator"] == "Suomen valtio"
    assert item["operator_wikidata"] == "Q33"


def test_commercial_tenants_never_take_city_operator():
    # SYNTHETIC: Kino Tapiola (cinema) and staff-restaurant (canteen) shapes.
    for category, department, municipality in (
        (Categories.CINEMA, "Espoon kaupunki", "espoo"),
        (Categories.CANTEEN, "Helsingin kaupunki", "helsinki"),
    ):
        _, item = operated(
            category,
            {"root_department": "d1", "municipality": municipality},
            {"d1": department},
        )
        assert "operator" not in item, category


def test_norlandia_brand():
    # Unit 80653.
    item = branded({"organizer_name": "Norlandia päiväkodit Oy", "name": {"fi": "Norlandia Vilja"}})
    assert item["brand"] == "Norlandia"
    assert item["brand_wikidata"] == "Q137463892"


def test_uff_brand_word_boundary():
    # Unit 80644.
    item = branded({"name": {"fi": "UFF Annankatu"}})
    assert item["brand"] == "UFF"
    assert item["brand_wikidata"] == "Q11899315"


def test_minibuffet_gets_no_uff_brand():
    # Unit 76247.
    item = branded({"name": {"fi": "Minibuffet"}})
    assert "brand" not in item


def test_kierratyskeskus_chain_brand():
    # Unit 80922.
    item = branded({"name": {"fi": "Pääkaupunkiseudun Kierrätyskeskus Tammisto"}})
    assert item["brand"] == "Pääkaupunkiseudun Kierrätyskeskus"
    assert item["brand_wikidata"] == "Q20920687"


def test_stara_recycling_gets_no_chain_brand():
    # Unit 9177.
    item = branded({"name": {"fi": "Stara kierrätyskeskus Liukumäentie"}})
    assert "brand" not in item


def test_spr_kontti_brand():
    # Unit 64076.
    item = branded({"organizer_name": "SPR Kontti", "name": {"fi": "SPR Kontti Espoo Merituuli"}})
    assert item["brand"] == "SPR Kontti"
    assert item["brand_wikidata"] == "Q409603"


def test_aimo_park_brand():
    # Unit 67707: organizer "Aimo Park Finland Oy / Q-park".
    item = branded({"organizer_name": "Aimo Park Finland Oy / Q-park", "name": {"fi": "Aimo Park, Vallila"}})
    assert item["brand"] == "Aimo Park"
    assert item["brand_wikidata"] == "Q126728228"


def test_chain_branch_splits():
    # Verified uniform "Brand separator Branch" chains: name splits, branch
    # carries the site (ref = sample unit). Guards (no branch, Outlet,
    # non-chain lookalikes) keep the full name.
    cases = (
        ("Aimo Park", "Aimo Park, Vallila", "Vallila", 67707),
        ("Jungle Juice Bar", "Jungle Juice Bar - Hertsi", "Hertsi", 72903),
        ("Kanniston Leipomo", "Kanniston Leipomo Sello", "Sello", 76929),
        ("Hanko Aasia", "Hanko Aasia Tripla", "Tripla", 61847),
        ("Paperikauppa Putinki", "Paperikauppa Putinki Hakaniemi", "Hakaniemi", 58491),
        ("Pizzeria Via Tribunali", "Pizzeria Via Tribunali Punavuori", "Punavuori", 72754),
        ("Levain", "Levain Ullanlinna", "Ullanlinna", 73512),
        ("Fazer Café", "Fazer Café Bulevardi", "Bulevardi", 69045),
        ("UFF", "UFF Annankatu", "Annankatu", 80644),
        ("Fida secondhand", "Fida secondhand Tammisto", "Tammisto", 80278),
        ("Metrosuutarit", "Metrosuutarit Tapiola", "Tapiola", 64199),
        ("Fonum", "Fonum Kamppi", "Kamppi", 64221),
        ("SPR Kontti", "SPR Kontti Espoo Galleria", "Espoo Galleria", 76073),
        ("Picnic", "Picnic Columbus", "Columbus", 79353),
        ("Musti ja Mirri", "Musti ja Mirri Stockmann", "Stockmann", 79233),
        ("Musti ja Murri", "Musti ja Murri Munkkivuori", "Munkkivuori", 79231),
        ("Robert's Coffee", "Robert's Coffee Arabia", "Arabia", 78779),
        ("24 Pesula", "24 Pesula Easton", "Easton", 79348),
        ("Eat Poke", "Eat Poke Kaari", "Kaari", 79305),
        ("Kultajousi", "Kultajousi Forum", "Forum", 79434),
        ("Laatukoru", "Laatukoru Itis", "Itis", 79453),
        ("Arnolds", "Arnolds REDI", "REDI", 78636),
        ("Partioaitta", "Partioaitta Tripla", "Tripla", 80642),
        ("Kidia", "Kidia Ainoa Espoo", "Ainoa Espoo", 71983),
        ("William K.", "William K. Mannerheimintie", "Mannerheimintie", 70609),
        ("Omena-hotelli", "Omena-hotelli Lönnrotinkatu", "Lönnrotinkatu", 24572),
        ("Tortilla House", "Tortilla House Kamppi", "Kamppi", 73478),
        ("Deliberi", "Deliberi Tapiola", "Tapiola", 72775),
        ("Ruohonjuuri", "Ruohonjuuri Itis", "Itis", 79862),
        ("Sizzle Station", "Sizzle Station Sello", "Sello", 72422),
        ("Finnfoto Galleria", "Finnfoto Galleria Kaari", "Kaari", 73149),
        ("Bär Bar", "Bär Bar Kasarmikatu", "Kasarmikatu", 78938),
        ("Mashiro", "Mashiro Viikki", "Viikki", 78986),
        ("Uuno", "Uuno Herttoniemi", "Herttoniemi", 78783),
        ("VillageWorks", "VillageWorks Ruoholahti", "Ruoholahti", 79262),
        ("Meeting Park", "Meeting Park Kamppi", "Kamppi", 72468),
        ("Innovation Home", "Innovation Home Arabia", "Arabia", 74152),
        ("Putte's Bar & Pizza", "Putte's Bar & Pizza Tikkurila", "Tikkurila", 71746),
        ("Boneless", "Boneless Vuosaari", "Vuosaari", 75177),
        ("Friends & Brgrs", "Friends & Brgrs Kulttuurikasarmi", "Kulttuurikasarmi", 77604),
        ("Gateau", "Gateau Rautatieasema", "Rautatieasema", 79024),
        ("Makaronitehdas", "Makaronitehdas Ainoa", "Ainoa", 72808),
        ("Suomalainen Kirjakauppa", "Suomalainen Kirjakauppa Kamppi", "Kamppi", 72803),
        ("Classic Pizza Restaurant", "Classic Pizza Restaurant Iso Omena", "Iso Omena", 72819),
        ("Noodle Story", "Noodle Story Freda", "Freda", 73669),
        ("Hemingway's", "Hemingway's Tennispalatsi", "Tennispalatsi", 73568),
        ("Delhi Rasoi", "Delhi Rasoi Tripla", "Tripla", 73567),
        ("Burger Company", "Burger Company Postitalo", "Postitalo", 80619),
        ("Brewster Bar", "Brewster Bar Roba", "Roba", 71724),
        ("Oishi18", "Oishi18 Töölö", "Töölö", 79504),
        ("Ristorante Limone", "Ristorante Limone Tripla", "Tripla", 73365),
        ("Bambu Sushi", "Bambu Sushi Konepaja", "Konepaja", 73481),
        ("The Pantry", "The Pantry Vallila", "Vallila", 79900),
        ("The Body Shop", "The Body Shop Kamppi", "Kamppi", 80691),
        ("Marimekko", "Marimekko Itäkeskus", "Itäkeskus", 80307),
        ("Tortilla Corner", "Tortilla Corner Mannerheimintie", "Mannerheimintie", 79015),
        ("Joe & the Juice", "Joe & the Juice Forum", "Forum", 78985),
        ("EuroPark", "EuroPark, P-WTC", "P-WTC", 67636),
        ("EuroPark", "EuroPark, P-Porttikeskus P8", "P-Porttikeskus P8", 67630),
        ("Finnkino", "Finnkino Tennispalatsi", "Tennispalatsi", 56616),
        ("Finnkino", "Finnkino Itis", "Itis", 66748),
        ("Finnkino", "Finnkino Maxim", "Maxim", 30169),
        ("Finnkino", "Finnkino Kinopalatsi", "Kinopalatsi", 24442),
        ("Scandic", "Scandic Espoo", "Espoo", 20876),
        ("Scandic", "Scandic Hakaniemi", "Hakaniemi", 24335),
        ("Clarion Hotel", "Clarion Hotel Helsinki", "Helsinki", 50693),
        ("Comfort Hotel", "Comfort Hotel Helsinki Airport", "Helsinki Airport", 75521),
        ("Holiday Inn", "Holiday Inn Helsinki - Expo", "Helsinki - Expo", 20436),
        ("Original Sokos Hotel", "Original Sokos Hotel Tripla", "Tripla", 61506),
        ("Solo Sokos Hotel", "Solo Sokos Hotel Pier 4", "Pier 4", 75878),
        ("Break Sokos Hotel", "Break Sokos Hotel Flamingo", "Flamingo", 25473),
        ("GLO Hotel", "GLO Hotel Sello", "Sello", 25477),
        ("Hiisi Hotel", "Hiisi Hotel Helsinki Jätkäsaari", "Helsinki Jätkäsaari", 75058),
        ("Hiisi Homes & Hotel", "Hiisi Homes & Hotel Helsinki Haaga", "Helsinki Haaga", 57594),
        ("Forenom Aparthotel Helsinki", "Forenom Aparthotel Helsinki Kamppi", "Kamppi", 43281),
        (
            "Forenom Serviced Apartments Helsinki",
            "Forenom Serviced Apartments Helsinki Lauttasaari",
            "Lauttasaari",
            76673,
        ),
        ("Forenom Hostel Helsinki", "Forenom Hostel Helsinki Pitäjänmäki", "Pitäjänmäki", 51224),
        ("Radisson Blu Hotel", "Radisson Blu Hotel, Espoo", "Espoo", 24250),
        ("Radisson Blu Seaside Hotel", "Radisson Blu Seaside Hotel, Helsinki", "Helsinki", 21199),
        ("Radisson RED", "Radisson RED Helsinki", "Helsinki", 73312),
        ("Citybox Hotel", "Citybox Hotel Helsinki", "Helsinki", 73127),
        ("Hotel Indigo", "Hotel Indigo Helsinki - Boulevard", "Helsinki - Boulevard", 44862),
        ("The Folks Hotel", "The Folks Hotel Konepaja", "Konepaja", 63288),
        ("Lapland Hotels", "Lapland Hotels Bulevardi", "Bulevardi", 55963),
        ("Home Hotel", "Home Hotel Katajanokka", "Katajanokka", 21031),
        ("Crowne Plaza", "Crowne Plaza Helsinki - Hesperia", "Helsinki - Hesperia", 20871),
        ("Ravintola Loru", "Ravintola Loru Lauttasaari", "Lauttasaari", 79718),
        ("Ravintola Konnichiwa", "Ravintola Konnichiwa Kamppi", "Kamppi", 79486),
        ("Krung Thep Thai Bistro", "Krung Thep Thai Bistro Kalasatama", "Kalasatama", 79236),
        ("Ravintola MoMo", "Ravintola MoMo Punavuori", "Punavuori", 70641),
        ("Ravintola Rioni", "Ravintola Rioni Espoo", "Espoo", 76658),
        ("Fat Lizard", "Fat Lizard Otaniemi", "Otaniemi", 63370),
        ("Rosso Pizza", "Rosso Pizza, Tikkurila", "Tikkurila", 78902),
        ("Amarillo", "Amarillo Tikkurila", "Tikkurila", 68787),
        ("Ravintola Haiku", "Ravintola Haiku Kämp Galleria", "Kämp Galleria", 72905),
        ("Stockmann", "Stockmann, Helsingin keskusta", "Helsingin keskusta", 20863),
        ("Rusta", "Rusta Helsinki - Lanterna", "Helsinki - Lanterna", 53147),
        ("Puuilo", "Puuilo Itäkeskus, Helsinki", "Itäkeskus, Helsinki", 68971),
        ("Food Market Herkku", "Food Market Herkku, Helsinki keskusta", "Helsinki keskusta", 54692),
        ("NP Housukauppa", "NP Housukauppa Tripla", "Tripla", 78955),
        ("Moomin Shop", "Moomin Shop Esplanadi", "Esplanadi", 73463),
        ("Heirol Shop", "Heirol Shop Helsinki", "Helsinki", 78954),
        ("Sinelli-myymälä", "Sinelli-myymälä, Itis", "Itis", 78685),
    )
    spider = make_spider()
    for brand, fi, branch, ref in cases:
        item = Feature()
        item["name"] = fi
        spider._apply_chain_branch(item, {"name": {"fi": fi}})
        assert item["name"] == brand, (ref, fi)
        assert item["branch"] == branch, (ref, fi)
        assert item["extras"]["official_name"] == fi, (ref, fi)
    # Guards: store-type branch, missing branch, non-chain lookalikes stay whole.
    for fi in (
        "Partioaitta Outlet",
        "Partioaitta Outlet Helsinki",
        "Fazer 8th Floor",
        "Minibuffet",
        "Amarillo",
        "Ravintola Rioni",
        "Finnkino Tennispalatsi (Finnkino Yritysmyynti)",
        "Comfort Hotel Sellon talkoolaituri",
    ):
        item = Feature()
        item["name"] = fi
        spider._apply_chain_branch(item, {"name": {"fi": fi}})
        assert item["name"] == fi, fi
        assert "branch" not in item, fi


def test_aimo_park_branch_split():
    # Chain name plus branch site split OSM-style (unit 67707 shape).
    spider = make_spider()
    item = Feature()
    item["name"] = "Aimo Park, Vallila"
    spider._apply_brand(
        item,
        {"organizer_name": "Aimo Park Finland Oy / Q-park", "name": {"fi": "Aimo Park, Vallila"}},
    )
    assert item["name"] == "Aimo Park"
    assert item["branch"] == "Vallila"
    assert item["extras"]["official_name"] == "Aimo Park, Vallila"


def test_finnkino_chain_brand():
    # Units 56616/66748/30169/24442: Finnkino cinemas carry the verified
    # chain brand (Q5450883, Finnish cinema chain); the corporate sales
    # office 20989 keeps its paren qualifier whole (pinned in the chain
    # table guards).
    item = branded({"name": {"fi": "Finnkino Tennispalatsi"}, "organizer_name": None})
    assert item["brand"] == "Finnkino"
    assert item["brand_wikidata"] == "Q5450883"


def test_scandic_chain_brand():
    # Unit 54709: Scandic hotels carry the verified chain brand (Q129391,
    # Swedish hotel chain). Start-anchored: "Marski by Scandic" (unit
    # 20877) and parking at Scandic hotels (unit 67632) stay unbranded.
    spider = make_spider()
    item = Feature()
    spider._apply_name(item, {"name": {"fi": "Scandic Meilahti"}, "service_nodes": []})
    spider._apply_brand(item, {"name": {"fi": "Scandic Meilahti"}, "organizer_name": None})
    assert item["name"] == "Scandic"
    assert item["branch"] == "Meilahti"
    assert item["extras"]["official_name"] == "Scandic Meilahti"
    assert item["brand"] == "Scandic"
    assert item["brand_wikidata"] == "Q129391"
    item = branded({"name": {"fi": "Marski by Scandic"}, "organizer_name": None})
    assert "brand" not in item
    item = branded({"name": {"fi": "EuroPark, P-Scandic Grand Marina"}, "organizer_name": "AutoParkki Norden Oy"})
    assert "brand" not in item


def test_chain_branch_swedish_parity():
    # Unit 73568: fi splits to branch, sv strips the same tail instead of
    # keeping the full form; the full forms live in official_name:sv/en.
    spider = make_spider()
    item = Feature()
    spider._apply_name(
        item,
        {
            "name": {
                "fi": "Hemingway's Tennispalatsi",
                "sv": "Hemingway's Tennispalatset",
                "en": "Hemingway's Tennispalatsi",
            },
            "service_nodes": [],
        },
    )
    spider._apply_brand(item, {"name": {"fi": "Hemingway's Tennispalatsi"}, "organizer_name": None})
    assert item["name"] == "Hemingway's"
    assert item["branch"] == "Tennispalatsi"
    assert item["extras"]["official_name"] == "Hemingway's Tennispalatsi"
    assert "name:sv" not in item["extras"]
    assert "name:en" not in item["extras"]
    assert item["extras"]["official_name:sv"] == "Hemingway's Tennispalatset"
    assert item["extras"]["official_name:en"] == "Hemingway's Tennispalatsi"


def test_ankkalampi_comma_site_split():
    # Units 29918/33747: private-chain daycares name the site after the
    # comma; the site is the venue. Self-referential tails (unit 46377)
    # stay whole.
    item = named(make_spider(), "Päiväkoti Ankkalampi, Punavuori", [879])
    assert item["name"] == "Päiväkoti Ankkalampi"
    assert item["located_in"] == "Punavuori"
    assert item["extras"]["official_name"] == "Päiväkoti Ankkalampi, Punavuori"
    item = named(
        make_spider(),
        "Päiväkoti Ankkalampi,Töölö - Duckies",
        [879],
        en="Daycare Ankkalampi,Töölö - Duckies",
    )
    assert item["name"] == "Päiväkoti Ankkalampi"
    assert item["located_in"] == "Töölö - Duckies"
    assert item["extras"]["name:en"] == "Daycare Ankkalampi"
    assert item["extras"]["official_name:en"] == "Daycare Ankkalampi,Töölö - Duckies"
    item = named(make_spider(), "Päiväkoti Ankkalampi,Mechelininkadun Ankkalampi-Ankdammen", [887])
    assert item["name"] == "Päiväkoti Ankkalampi,Mechelininkadun Ankkalampi-Ankdammen"
    assert "located_in" not in item


def test_spaced_housenumber_letter_folds():
    # Units 26123/68882/64842: the lowercase appendix is spaced off the
    # number ("Mannerheimintie 13 a A"); it belongs to the housenumber
    # (13a), the last token is the staircase. Uppercase middles
    # ("Lummetie 2 B C", unit 68880) never fold.
    item = addressed(make_spider(), "Mannerheimintie 13 a A")
    assert item["street"] == "Mannerheimintie"
    assert item["housenumber"] == "13a"
    assert item["unit"] == "A"
    item = addressed(make_spider(), "Lummetie 2 b C")
    assert item["housenumber"] == "2b"
    assert item["unit"] == "C"


def test_memorial_slash_names_title():
    # Unit 23246 is the Lähde memorial to president Kekkonen: the title
    # side is the name, the dedication is not a venue. Memorial-first
    # pairs (unit 23309) keep the existing facility-name split.
    item = named(make_spider(), "Lähde / UKK-monumentti")
    assert item["name"] == "Lähde"
    assert "located_in" not in item
    assert item["extras"]["official_name"] == "Lähde / UKK-monumentti"
    item = named(make_spider(), "Itä ja Länsi / J. K. Paasikiven muistomerkki")
    assert item["name"] == "Itä ja Länsi"
    assert "located_in" not in item
    item = named(make_spider(), "Juutalaispakolaisten muistomerkki / Apua anovat kädet")
    assert item["name"] == "Apua anovat kädet"
    assert item["located_in"] == "Juutalaispakolaisten muistomerkki"


def test_tori_filed_as_marketplace_is_square():
    # Units 34753/34752/34723: a tori is a square first, market function
    # or not (cf. Kauppatori itself, tagged square via the sights node).
    item = full(make_spider(), "Töölöntori", [84, 753])
    assert item.get_tag("tourism") == "attraction"
    assert item.get_tag("place") == "square"
    assert item.get_tag("amenity") is None


def test_bilingual_translation_slash_strips_fi():
    # Units 23168/29944: the en field repeats fi before the translation
    # ("Oodi 60 000 järvelle / The Ode ..."); the fi prefix is not a
    # venue, and the venue must never equal the name.
    item = named(
        make_spider(),
        "Oodi 60 000 järvelle",
        [2006],
        en="Oodi 60 000 järvelle / The Ode to the 60,000 Lakes",
    )
    assert item["name"] == "Oodi 60 000 järvelle"
    assert "located_in" not in item
    assert item["extras"]["name:en"] == "The Ode to the 60,000 Lakes"
    assert item["extras"]["official_name:en"] == "Oodi 60 000 järvelle / The Ode to the 60,000 Lakes"
    item = named(make_spider(), "Unelma", [2006], en="Unelma / Dream")
    assert "located_in" not in item
    assert item["extras"]["name:en"] == "Dream"


def test_paren_slash_splits_outside_parens():
    # Unit 42121: the parenthetical holds its own slash; the facility
    # split ignores slashes inside parens instead of naming the unit
    # "Muistomerkki)".
    item = named(make_spider(), "Uimastadion kuntorata / Ulkokuntosali (Pohjoinen Stadiontie / Muistomerkki)")
    assert item["name"] == "Ulkokuntosali (Pohjoinen Stadiontie / Muistomerkki)"
    assert item["located_in"] == "Uimastadion kuntorata"
    assert (
        item["extras"]["official_name"] == "Uimastadion kuntorata / Ulkokuntosali (Pohjoinen Stadiontie / Muistomerkki)"
    )


def test_chessboard_comma_place_split():
    # Units 63009/73192: street-furniture chessboards name their place
    # after the comma. Reversed tails (unit 67825) stay whole.
    item = named(make_spider(), "Shakkilauta, Tilkantori", [2236])
    assert item["name"] == "Shakkilauta"
    assert item["located_in"] == "Tilkantori"
    assert item["extras"]["official_name"] == "Shakkilauta, Tilkantori"
    item = named(make_spider(), "Shakkilauta, Hesperianpuisto", [2236])
    assert item["name"] == "Shakkilauta"
    assert item["located_in"] == "Hesperianpuisto"
    item = named(make_spider(), "Puistokenttä Koiruohonpuisto, shakkilauta", [648])
    assert item["name"] == "Puistokenttä Koiruohonpuisto, shakkilauta"
    assert "located_in" not in item


def test_staff_canteen_institution_split():
    # Units 8817/8790/8845: staff canteens at host institutions name the
    # site after the comma. Appositive proper names (unit 8796) and bare
    # descriptors (units 8843/8797) stay whole.
    item = named(make_spider(), "Henkilöstöravintola, Terveyden ja hyvinvoinnin laitos (THL)", [183])
    assert item["name"] == "Henkilöstöravintola"
    assert item["located_in"] == "Terveyden ja hyvinvoinnin laitos (THL)"
    assert item["extras"]["official_name"] == "Henkilöstöravintola, Terveyden ja hyvinvoinnin laitos (THL)"
    item = named(make_spider(), "Henkilöstöravintola, Sähkötalo", [183])
    assert item["name"] == "Henkilöstöravintola"
    assert item["located_in"] == "Sähkötalo"
    item = named(make_spider(), "Henkilöstöravintola, ravintola Onnikka", [183])
    assert item["name"] == "Henkilöstöravintola, ravintola Onnikka"
    assert "located_in" not in item
    item = named(make_spider(), "Henkilöstöravintola, Holkki", [183])
    assert item["name"] == "Henkilöstöravintola, Holkki"
    assert "located_in" not in item


def test_health_service_first_comma():
    # Units 69833/69681: multi-segment service heads split at the first
    # comma. Description tails (unit 69236) stay whole.
    item = named(make_spider(), "Opiskeluhuolto, Karjaan yhteiskoulu, lukio", [1374])
    assert item["name"] == "Opiskeluhuolto"
    assert item["located_in"] == "Karjaan yhteiskoulu, lukio"
    item = named(make_spider(), "Opiskeluhuolto, Ammattiopisto Live, päärakennus", [1374])
    assert item["name"] == "Opiskeluhuolto"
    assert item["located_in"] == "Ammattiopisto Live, päärakennus"
    item = named(make_spider(), "Opiskeluterveydenhuolto, keskitetty palvelu Espoo ja Kauniainen", [1374])
    assert item["name"] == "Opiskeluterveydenhuolto, keskitetty palvelu Espoo ja Kauniainen"
    assert "located_in" not in item


def test_translation_venue_holding_name_skipped():
    # Unit 22996: the en field joins fi and en with a spaceless slash; the
    # fi-holding "venue" is the name itself, not a host.
    item = named(
        make_spider(),
        "Crescendo / Vuoden 1918 Kansalaissodan uhrien muistomerkki",
        [2006],
        en="Crescendo (Vuoden 1918 Kansalaissodan uhrien muistomerkki)/ A Memorial to those who fell in the 1918",
    )
    assert item["name"] == "Crescendo"
    assert "located_in" not in item
    assert item["extras"]["name:en"] == "A Memorial to those who fell in the 1918"


def test_school_gloss_stripped_from_venue():
    # Unit 50343: the en field glosses the venue type ("(school)").
    item = named(
        make_spider(),
        "Juvanpuiston koulun frisbeegolfrata (3)",
        [578],
        en="Juvanpuiston koulu (school) / Disc golf course (3)",
    )
    assert item["located_in"] == "Juvanpuiston koulu"


def test_street_address_venue_dropped():
    # Unit 45330: bare addresses parse into street/housenumber, never venue.
    item = named(make_spider(), "Kurkisuontie 2 / Hiekkakenttä")
    assert item["name"] == "Hiekkakenttä"
    assert "located_in" not in item


def test_therapy_site_split():
    # Unit 69066: therapy at a named site names the service. Sub-units
    # naming their own therapy (unit 69061) keep the default split.
    item = named(make_spider(), "Lasten toimintaterapia/Länsi-Pasila", [1038])
    assert item["name"] == "Lasten toimintaterapia"
    assert item["located_in"] == "Länsi-Pasila"
    item = named(make_spider(), "Laakson toimintaterapia/Laakson neurologinen toimintaterapia", [1038])
    assert item["name"] == "Laakson neurologinen toimintaterapia"
    assert item["located_in"] == "Laakson toimintaterapia"


def test_service_desk_names_service():
    # Unit 71716: a service desk at a city hall names the service.
    item = named(make_spider(), "Karkkilan kaupungintalo/ sosiaalitoimisto", [851])
    assert item["name"] == "sosiaalitoimisto"
    assert item["located_in"] == "Karkkilan kaupungintalo"


def test_spaceless_debris_facility_stays_whole():
    # Unit 68047: a spaceless lowercase qualifier is debris, not a facility.
    item = named(make_spider(), "Nuorten vastaanotto Kallio/vaativa", [789])
    assert item["name"] == "Nuorten vastaanotto Kallio/vaativa"
    assert "located_in" not in item


def test_surface_last_segment_names_middle():
    # Unit 60097: a surface word as last segment names the middle facility.
    item = named(make_spider(), "Myllypuron liikuntapuisto / Baseball-kenttä / nurmi", [659])
    assert item["name"] == "Baseball-kenttä"
    assert item["located_in"] == "Myllypuron liikuntapuisto"


def test_website_scheme_added():
    # SYNTHETIC (feed has no schemeless www left).
    item = contacted({"www": {"fi": "www.hel.fi/palvelukartta"}})
    assert item["website"] == "https://www.hel.fi/palvelukartta"


def test_website_bad_scheme_rejected():
    # SYNTHETIC bad-scheme website.
    item = contacted({"www": {"fi": "ftp://x.fi/file"}})
    assert "website" not in item


def test_website_invalid_hostnames_rejected():
    # Units 66055 (comma typo) and 68883/64153/47295 (punycode): the
    # pipeline fails the build on these, so the spider drops the field.
    for raw in (
        "http://www,kirkkonummi.fi",
        "http://www.xn--tlnverhoomo-rfbab.fi/",
        "http://xn--pivkotipolku-gcbc.fi/index.html",
        "https://www.xn--polkupyrkirppis-7kb81a.fi/",
    ):
        assert "website" not in contacted({"www": {"fi": raw}}), raw
    item = contacted({"www": {"fi": "https://www.hel.fi/palvelukartta"}})
    assert item["website"] == "https://www.hel.fi/palvelukartta"


def test_website_falls_back_to_sv():
    # SYNTHETIC (no bad-fi plus good-sv shape in feed): a bad fi hostname
    # must not block a good sv one.
    item = contacted({"www": {"fi": "http://www.xn--tlnverhoomo-rfbab.fi/", "sv": "https://www.hel.fi/sv"}})
    assert item["website"] == "https://www.hel.fi/sv"


def test_website_string_shape_accepted():
    # SYNTHETIC (feed www is always a dict).
    item = contacted({"www": "espoo.fi"})
    assert item["website"] == "https://espoo.fi"


def test_phone_string_and_list():
    # SYNTHETIC phone string/list shapes.
    assert contacted({"phone": "+358 9 310 42578"})["phone"] == "+358 9 310 42578"
    assert contacted({"phone": ["+358 9 310 1", "+358 9 310 2"]})["phone"] == "+358 9 310 1"


def test_email_obfuscation_reversed():
    # Unit 28920.
    item = contacted({"email": "lansi-uusimaa.edunvalvonta(at)oikeus.fi"})
    assert item["email"] == "lansi-uusimaa.edunvalvonta@oikeus.fi"


def test_email_invalid_rejected():
    # SYNTHETIC invalid email.
    item = contacted({"email": "not-an-email"})
    assert "email" not in item


def test_parking_plain_capacity():
    # Unit 80707.
    item = parked("Pysäköintialue Soukankuja", "5 pysäköintipaikkaa")
    assert item["extras"]["capacity"] == "5"


def test_parking_reversed_counts():
    # Unit 67671: noun-first counts ("Pysäköintipaikkoja: 165") plus a
    # zero disabled count (no wheelchair tag for zero).
    item = parked("Ulkoalue", "Pysäköintipaikkoja: 165\nInva-paikat: 0")
    assert item["extras"]["capacity"] == "165"
    assert "capacity:disabled" not in item["extras"]
    assert "wheelchair" not in item["extras"]
    # SYNTHETIC nonzero disabled count.
    item = parked("Ulkoalue", "Pysäköintipaikkoja: 10\nInva-paikat: 2")
    assert item["extras"]["capacity"] == "10"
    assert item["extras"]["capacity:disabled"] == "2"
    assert item["extras"]["wheelchair"] == "designated"


def test_parking_disabled_only_capacity():
    # Unit 80685.
    item = parked("Esteetön pysäköintialue Kampusraitti", "3 esteetöntä autopaikkaa")
    assert item["extras"]["capacity:disabled"] == "3"
    assert item["extras"]["wheelchair"] == "designated"
    assert "capacity" not in item["extras"]


def test_park_ride_only_for_liitynta():
    # SYNTHETIC P-lot name and capacity text.
    item = parked("Liityntäpysäköinti P1", "500 autopaikkaa")
    assert item["extras"]["park_ride"] == "yes"
    assert item["extras"]["capacity"] == "500"
    assert "park_ride" not in parked("Pysäköintialue LP 12", "20 autopaikkaa")["extras"]


def test_end_date_invalid_guarded():
    # SYNTHETIC: impossible date.
    spider = make_spider()
    item = Feature()
    spider._apply_end_date(item, {"name": {"fi": "Paikka, toiminta päättyy 31.2.2026"}})
    assert "end_date" not in item["extras"]


def test_test_records_dropped():
    # Units 80731 and 75350.
    spider = make_spider()
    for fi in ("Henna testaa 2", "Esteettömyystestipiste"):
        assert (
            spider._build_item(
                {
                    "id": 1,
                    "name": {"fi": fi},
                    "service_nodes": [324],
                    "location": {"coordinates": [24.9, 60.1]},
                }
            )
            is None
        )
    assert spider.crawler.stats.get_value("atp/helsinki_servicemap_fi/dropped/test_data") == 2


def test_protest_like_names_kept():
    # SYNTHETIC: no protesti/contest unit in feed.
    spider = make_spider()
    item = spider._build_item(
        {
            "id": 2,
            "name": {"fi": "Protesti-tapahtuma ohjelmaa"},
            "service_nodes": [360],
            "location": {"coordinates": [24.9, 60.1]},
        }
    )
    assert item is not None
    assert item["name"] == "Protesti-tapahtuma ohjelmaa"
    assert item.get_tag("amenity") == "theatre"
    assert spider.crawler.stats.get_value("atp/helsinki_servicemap_fi/dropped/test_data") == 0


def test_excluded_subtrees_dropped():
    # Units 80961 [768], 77671 [582], 80786 Villinki [71, 502].
    spider = make_spider()
    for fi, nodes in (
        ("Tietovisa-palvelun järjestämispaikka", [768]),
        ("Niskalan arboretumin kävelyreitti", [582]),
        ("Villinki", [71, 502]),
    ):
        assert (
            spider._build_item(
                {
                    "id": 3,
                    "name": {"fi": fi},
                    "service_nodes": nodes,
                    "location": {"coordinates": [24.9, 60.1]},
                }
            )
            is None
        )


def test_mixed_excluded_and_tabled_is_kept():
    # SYNTHETIC school-kitchen/venue combo, constructed id 4.
    # A school kitchen plus a real facility survives exclusion.
    spider = make_spider()
    item = spider._build_item(
        {
            "id": 4,
            "name": {"fi": "Koulu ja keittiö"},
            "service_nodes": [1376, 1097],
            "location": {"coordinates": [24.9, 60.1]},
        }
    )
    assert item is not None
    assert item.get_tag("amenity") == "school"
    assert spider.crawler.stats.get_value("atp/helsinki_servicemap_fi/dropped/non_place") == 0


def test_not_displayed_string_and_dict_dropped():
    # BowlCircus Sello / biljardisali is unit 80945; id/coords/nodes constructed.
    spider = make_spider()
    for contract in ("NOT_DISPLAYED", {"id": "NOT_DISPLAYED"}):
        assert (
            spider._build_item(
                {
                    "id": 5,
                    "name": {"fi": "BowlCircus Sello / biljardisali"},
                    "service_nodes": [2426],
                    "contract_type": contract,
                    "location": {"coordinates": [24.8, 60.2]},
                }
            )
            is None
        )


def test_missing_coords_dropped():
    # Unit 80937 shape.
    spider = make_spider()
    assert spider._build_item({"id": 6, "name": {"fi": "Sote-auto"}, "service_nodes": [1029], "location": None}) is None


# ---- Findings from the second review round ---------------------------------


def test_island_district_suffixes_are_not_islands():
    # Units 79341 (24 Pesula Vuosaari), 77927 (Laguuni Lauttasaari),
    # 72408 (Parkour Akatemia Lauttasaari), 59906 (Alepa Kulosaari),
    # 71722 (Siltasaari 10): mainland districts ending in -saari.
    spider = make_spider()
    for fi, nodes in (
        ("24 Pesula Vuosaari", [750]),
        ("Laguuni Lauttasaari", [2246]),
        ("Alepa Kulosaari", [750]),
        ("Siltasaari 10", [750]),
    ):
        item = Feature()
        unit = {"name": {"fi": fi}, "service_nodes": nodes}
        spider._apply_name(item, unit)
        spider._apply_category(item, unit)
        assert item.get_tag("place") is None, fi


def test_laundry_rescue():
    # Units 79341 (24 Pesula Vuosaari) and similar district laundromats.
    item = full(make_spider(), "24 Pesula Vuosaari", [750])
    assert item.get_tag("shop") == "laundry"


def test_neuvola_rescue_is_clinic():
    # Unit 61678 shape: Neuvolan psykologipalvelut Vuosaari.
    item = full(make_spider(), "Neuvolan psykologipalvelut Vuosaari", [1041])
    assert item.get_tag("amenity") == "clinic"


def test_boat_rental_rescue():
    # Unit 68207 shape: Seapoint Venevuokraus Liuskaluoto.
    item = full(make_spider(), "Seapoint Venevuokraus Liuskaluoto", [748, 591])
    assert item.get_tag("amenity") == "boat_rental"


def test_allotment_rescue():
    # SYNTHETIC viljelypalstat shapes (cf. units 77565/77564).
    # Tullisaari/Vartiosaari viljelypalstat shapes.
    item = full(make_spider(), "Tullisaari, viljelypalstat", [548])
    assert item.get_tag("landuse") == "allotments"


def test_school_filed_playground_is_playground():
    # Unit 80727: Leikkipuisto Rusettipuisto (same playground rule as daycare filing).
    spider = make_spider({976: 975, 975: 868, 979: 975, 2134: 1181, 1181: 1098, 1098: 1097})
    item = full(spider, "Leikkipuisto Rusettipuisto", [976, 979, 2134])
    assert item.get_tag("leisure") == "playground"


def test_flea_market_beats_events_filing():
    # Unit 80667: Tapanilan Kirppis.
    item = full(make_spider(), "Tapanilan Kirppis", [82, 750, 2173])
    assert item.get_tag("shop") == "second_hand"


def test_food_museum_compound_is_museum():
    # SYNTHETIC (no live unit): Hotelli- ja ravintolamuseo.
    item = full(make_spider(), "Hotelli- ja ravintolamuseo", [736])
    assert item.get_tag("tourism") == "museum"


def test_restaurant_named_museum_keeps_food():
    # SYNTHETIC: Ravintola Museo.
    item = full(make_spider(), "Ravintola Museo", [751])
    assert item.get_tag("amenity") == "restaurant"


def test_dotted_apartment_tail():
    # SYNTHETIC (unit 77047's shape is excluded): Valhallankatu 4.A.9.
    item = addressed(make_spider(), "Valhallankatu 4.A.9")
    assert item["housenumber"] == "4"
    assert item["unit"] == "A.9"


def test_trailing_dash_stripped():
    # Unit 75283 shape: Kutomokuja 3 -.
    item = addressed(make_spider(), "Kutomokuja 3 -")
    assert item["housenumber"] == "3"
    assert item["street"] == "Kutomokuja"


def test_degenerate_comma_address_does_not_crash():
    # SYNTHETIC degenerate punctuation address.
    spider = make_spider()
    for raw in (",", ",,", " , "):
        item = Feature()
        assert spider._apply_comma_address(item, raw) is True
        assert "street" not in item
        assert "housenumber" not in item
        assert "street_address" not in item
        assert "addr:place" not in item["extras"]


def test_walk_cycle_terminates():
    # SYNTHETIC parent loop.
    spider = make_spider({1: 2, 2: 1})
    assert list(spider._walk(1)) == [1, 2]


def test_follow_pagination_loop_raises():
    # SYNTHETIC repeated next URL.
    from scrapy.exceptions import CloseSpider

    spider = make_spider()
    spider.seen_next = set()
    assert spider._follow({"next": None}, None, None) is None
    spider._follow({"next": "https://x/?page=2"}, None, None)
    try:
        spider._follow({"next": "https://x/?page=2"}, None, None)
    except CloseSpider:
        return
    raise AssertionError("expected CloseSpider on repeated next URL")


def test_swedish_ab_org_stripped():
    # Ab strips exactly like ry/oy when the remainder names a venue.
    # SYNTHETIC Foo/Bar names.
    spider = make_spider()
    assert spider._clean_name("Foo päiväkoti, Bar Ab") == "Foo päiväkoti"
    assert spider._clean_name("Foo paikka, Bar Ab") == "Foo paikka, Bar Ab"


def test_slash_krs_tail_stripped():
    # SYNTHETIC floor-tail address.
    item = addressed(make_spider(), "Katu 5 / 2. krs")
    assert item["housenumber"] == "5"


def test_dash_entrance_tail_stripped():
    # SYNTHETIC entrance-tail address.
    item = addressed(make_spider(), "Katu 5 - sisäänkäynti B")
    assert item["housenumber"] == "5"


def test_mid_string_rak_tail_stripped():
    # SYNTHETIC building-tail address.
    item = addressed(make_spider(), "Katu 5 rak B")
    assert item["housenumber"] == "5"


def test_school_category_branches():
    spider = make_spider()
    assert spider._school_category("X opisto") == Categories.COLLEGE
    assert spider._school_category("X päiväkoti") == Categories.KINDERGARTEN
    assert spider._school_category("X peruskoulu") == Categories.SCHOOL
    assert spider._school_category("koulutus") is None
    # Routed through the full path: office-filed school takes college,
    # while koulutus-only keeps its office filing. SYNTHETIC X-names.
    assert full(make_spider(), "X opisto", [2004]).get_tag("amenity") == "college"
    assert full(make_spider(), "koulutus", [2004]).get_tag("office") == "government"


def test_wellness_routes_through_full_path():
    # Unit 79687 shape: SAUNA-filed jooga/kauneus units refine by name.
    assert full(make_spider(), "Kauneushoitola Bella", [2168]).get_tag("shop") == "beauty"


def test_machine_name_swedish_branch():
    # SYNTHETIC: sv ticket-machine name alongside the fi identifier.
    item = named(
        make_spider(),
        "Pysäköintilippuautomaatti 591",
        sv="Parkeringsbiljettautomat 591, kortbetalning",
    )
    assert item["name"] == "Pysäköintilippuautomaatti 591"
    assert item["extras"]["name:sv"] == "Parkeringsbiljettautomat 591"


def test_wellness_branches():
    # SYNTHETIC wellness-service names.
    spider = make_spider()
    cases = [
        ("kauneushoitola bella", Categories.SHOP_BEAUTY),
        ("tatuointistudio x", Categories.SHOP_TATTOO),
        ("hierontapiste", Categories.SHOP_MASSAGE),
        ("fysioyksikkö", Categories.PHYSIOTHERAPIST),
        ("joogastudio a16", Categories.GYM),
    ]
    for text, expected in cases:
        assert spider._wellness_category(Categories.SAUNA, text) == expected, text
    # Keepers fall through to their owning rules (spa, trade) or the default.
    assert spider._wellness_category(Categories.SAUNA, "kellumo") is None
    assert spider._wellness_category(Categories.SAUNA, "hilla helsinki - day spa & shop") is None
    assert spider._wellness_category(Categories.SAUNA, "pranama kallio") is Categories.GENERIC_POI


def test_activity_branches():
    # SYNTHETIC activity-area names.
    spider = make_spider()
    assert (
        spider._activity_category(Categories.LEISURE_FITNESS_STATION, "keskuksen lähiliikuntapaikka miniareena", "")
        == Categories.LEISURE_PITCH
    )
    assert (
        spider._activity_category(Categories.LEISURE_FITNESS_STATION, "koulun lähiliikuntapaikka", "")
        == Categories.LEISURE_PLAYGROUND
    )
    assert (
        spider._activity_category(Categories.LEISURE_SPORTS_CENTRE, "puiston jumppa-alue", "")
        == Categories.LEISURE_FITNESS_STATION
    )


def test_civic_branches():
    # Espoonlahden Espoo-info is unit 53543; the other names are constructed.
    spider = make_spider()
    assert spider._civic_category(Categories.COMMUNITY_CENTRE, "neuvonta piste") == Categories.OFFICE_GOVERNMENT
    assert spider._civic_category(Categories.COMMUNITY_CENTRE, "kahvila deli") == Categories.CAFE
    assert spider._civic_category(Categories.SOCIAL_FACILITY, "miepä toiminta") == Categories.COMMUNITY_CENTRE
    item = full(make_spider(), "Espoonlahden Espoo-info", [319])
    assert item.get_tag("tourism") == "information"


def test_bowling_refine_beats_events_filing():
    # Unit 80771: Talin keilahalli.
    item = full(make_spider(), "Talin keilahalli", [2246, 2173])
    assert item.get_tag("leisure") == "bowling_alley"


def test_yths_refine_beats_nurse_filing():
    # Unit 46260: YTHS Otaniemi.
    item = full(make_spider(), "YTHS Otaniemi", [2167, 2166])
    assert item.get_tag("amenity") == "clinic"


def test_groomer_and_photo_rescue():
    # Units 78860 (BONJOUR Koiratrimmaamo Olari) and 72392 (JAS Kamerakauppa).
    spider = make_spider()
    item = Feature()
    spider._apply_name_rescue(item, {"name": {"fi": "BONJOUR Koiratrimmaamo Olari"}, "service_nodes": [99999]})
    assert item.get_tag("shop") == "pet_grooming"
    item = Feature()
    spider._apply_name_rescue(item, {"name": {"fi": "JAS Kamerakauppa"}, "service_nodes": [99999]})
    assert item.get_tag("shop") == "photo"


def test_murri_spelling_rescue():
    # Unit 79231: feed spells the chain "Murri" here.
    item = full(make_spider(), "Musti ja Murri Munkkivuori", [99999])
    assert item.get_tag("shop") == "pet"


def test_swedish_comma_street_tail_dropped():
    # Unit 71585: Alueellinen keräyspiste, Malmgatan 20-21.
    item = named(make_spider(), "Alueellinen keräyspiste, Malmgatan 20-21")
    assert item["name"] == "Alueellinen keräyspiste"
    assert "located_in" not in item


def test_activites_typo_never_splits():
    # Unit 74744: feed misspells "activities".
    item = named(make_spider(), "After-school activites / Comprehensive School Norsen")
    assert item["name"] == "After-school activites / Comprehensive School Norsen"
    assert "located_in" not in item


def test_swedish_park_ride_name():
    # Unit 58515 shape: anslutning lives in the sv name.
    spider = make_spider()
    item = Feature()
    apply_category(Categories.PARKING, item)
    spider._apply_parking_capacity(
        item,
        {
            "name": {"fi": "Sähkön latauspiste", "sv": "Laddstation, anslutningsparkering"},
            "description": {"fi": "10 autopaikkaa"},
        },
    )
    assert item["extras"]["park_ride"] == "yes"


def test_wilderness_hut_refine():
    # SYNTHETIC: hut noun filed under the generic park fallback.
    item = full(make_spider(), "Eräkämppä", [711])
    assert item.get_tag("tourism") == "wilderness_hut"


def test_no_premises_branches():
    # SYNTHETIC no-premises names.
    spider = make_spider()
    assert spider._has_no_premises(Categories.SOCIAL_FACILITY, "puhelinpalvelu X") is True
    assert spider._has_no_premises(Categories.CLINIC, "liikkuva yksikkö") is True
    assert spider._has_no_premises(Categories.COMMUNITY_CENTRE, "kirjasto kerho") is True
    assert spider._has_no_premises(Categories.OFFICE_GOVERNMENT, "opetuspaikka X") is True
    assert spider._has_no_premises(Categories.PLACE_OF_WORSHIP, "krypta") is True
    assert spider._has_no_premises(Categories.CLINIC, "tavallinen vastaanotto") is False


def test_facility_correction_spa():
    # SYNTHETIC spa name on a sauna filing.
    spider = make_spider()
    assert spider._facility_correction(Categories.SAUNA, set(), "day spa helsinki") == Categories.SHOP_BEAUTY_SPA


def test_facility_correction_health_food():
    # SYNTHETIC health-food filing names.
    spider = make_spider()
    assert spider._facility_correction(Categories.SHOP_HEALTH_FOOD, set(), "hammas kauppa") == Categories.DENTIST
    assert spider._facility_correction(Categories.SHOP_HEALTH_FOOD, set(), "terveysasema X") == Categories.CLINIC


def test_facility_correction_caravan_island():
    # SYNTHETIC island-named caravan filing.
    spider = make_spider()
    assert spider._facility_correction(Categories.CARAVAN_SITE, set(), "saari leirintä") is None


def test_facility_correction_food_in_university():
    # SYNTHETIC restaurant-at-university name.
    spider = make_spider()
    matched = {751, 1097}
    assert spider._facility_correction(Categories.CLINIC, matched, "ravintola yliopisto") == Categories.RESTAURANT


def test_university_branches():
    # SYNTHETIC university unit names.
    spider = make_spider()
    cat = Categories.UNIVERSITY
    assert spider._university_category(cat, "vahtimestarit") == Categories.OFFICE_ADMINISTRATIVE
    assert spider._university_category(cat, "terveystalo") == Categories.CLINIC
    assert spider._university_category(cat, "vierastalo") == Categories.TOURISM_GUEST_HOUSE
    assert spider._university_category(cat, "dipoli") == Categories.BUILDING_UNIVERSITY
    assert spider._university_category(cat, "kandidaattikeskus") == Categories.BUILDING_UNIVERSITY
    assert spider._university_category(cat, "aalto arts kandidaattikeskus") == Categories.OFFICE_ADMINISTRATIVE
    assert spider._university_category(cat, "fysiikan laitos") is None


def test_clinic_branches():
    # SYNTHETIC clinic names.
    spider = make_spider()
    assert spider._clinic_category(Categories.CLINIC, "vertaistuki ryhmä") == Categories.SOCIAL_FACILITY
    assert spider._clinic_category(Categories.CLINIC, "X palvelun järjestämispaikka") == Categories.COMMUNITY_CENTRE
    assert spider._clinic_category(Categories.CLINIC, "tavallinen") is None


def test_park_branches():
    # SYNTHETIC park/sight names.
    spider = make_spider()
    assert (
        spider._park_category(Categories.TOURISM_ATTRACTION, "hakaniementori") == Categories.TOURISM_ATTRACTION_SQUARE
    )
    assert spider._park_category(Categories.TOURISM_ATTRACTION, "konttori") is None
    assert spider._park_category(Categories.COMMUNITY_CENTRE, "kalasatamanpuisto") == Categories.LEISURE_PARK
    assert (
        spider._park_category(Categories.LEISURE_SPORTS_CENTRE, "stora herrö / uimaranta") == Categories.NATURAL_BEACH
    )


def test_activity_playground_with_gear():
    # SYNTHETIC playground-with-gear name.
    spider = make_spider()
    assert (
        spider._activity_category(Categories.LEISURE_FITNESS_STATION, "leikkipuisto keskus", "")
        == Categories.LEISURE_PLAYGROUND
    )


def test_wellness_barber():
    # SYNTHETIC barber filing name.
    spider = make_spider()
    assert spider._wellness_category(Categories.SAUNA, "parturi next century") == Categories.SHOP_HAIRDRESSER


def test_civic_resident_room_and_parish_house():
    # SYNTHETIC resident-room and parish-house names.
    spider = make_spider()
    assert spider._civic_category(Categories.OFFICE_GOVERNMENT, "asukastila kallio") == Categories.COMMUNITY_CENTRE
    assert spider._civic_category(Categories.PLACE_OF_WORSHIP, "seurakuntien talo") == Categories.OFFICE_GOVERNMENT


def test_staff_canteen_keeps_filing():
    # SYNTHETIC staff-canteen name.
    item = full(make_spider(), "Henkilöstöravintola Merta", [183])
    assert item.get_tag("amenity") == "canteen"


def test_daycare_subtag():
    # Unit 55864 (ryhmäperhepäiväkoti subtag).
    item = subtagged("Venäläis-suomalainen ryhmäperhepäiväkoti Pieni Maa", Categories.KINDERGARTEN)
    assert item["extras"]["kindergarten"] == "group_family_daycare"


def test_stairs_subtag():
    # Unit 80329 (kuntoportaat subtag).
    item = subtagged("Aino Acktén puisto / Kuntoportaat", Categories.LEISURE_FITNESS_STATION)
    assert item["extras"]["fitness_station"] == "stairs"


def test_arboretum_subtag():
    # Unit 54910 (Niskalan arboretum subtag).
    item = subtagged("Niskalan arboretum", Categories.LEISURE_GARDEN)
    assert item["extras"]["garden:type"] == "arboretum"


def test_mural_vs_graffiti_subtags():
    # SYNTHETIC mural/graffiti names.
    assert subtagged("Kallion muraali", Categories.TOURISM_ARTWORK)["extras"]["artwork_type"] == "mural"
    assert subtagged("Kallion katutaide", Categories.TOURISM_ARTWORK)["extras"]["artwork_type"] == "graffiti"


def test_voucher_service_drops_name():
    # SYNTHETIC voucher-service organizer.
    _, item = operated(
        Categories.KINDERGARTEN,
        {"displayed_service_owner_type": "VOUCHER_SERVICE", "organizer_name": "Pilke Oy", "municipality": "espoo"},
    )
    assert "operator" not in item
    assert item["extras"]["operator:type"] == "private"


def test_junk_organizer_variants_dropped():
    # SYNTHETIC junk organizer variants.
    spider = make_spider()
    for junk in ("yksityinen", "yksityinen palveluntuottaja", "yksityisen", "VALTIO"):
        item = Feature()
        apply_category(Categories.CLINIC, item)
        spider._apply_operator(item, {"organizer_name": junk, "municipality": "helsinki"})
        assert "operator" not in item, junk


def test_parenthetical_operator_keeps_wikidata():
    # SYNTHETIC: department name with a parenthetical suffix.
    _, item = operated(
        Categories.LIBRARY,
        {"organizer_name": "Helsingin kaupunki (kaupunginkanslia)", "municipality": "helsinki"},
    )
    assert item["operator_wikidata"] == "Q1757"


def test_matching_city_operator_kept():
    # SYNTHETIC matching city/municipality pair.
    _, item = operated(
        Categories.LIBRARY,
        {"root_department": "d1", "municipality": "espoo"},
        {"d1": "Espoon kaupunki"},
    )
    assert item["operator"] == "Espoon kaupunki"
    assert item["operator_wikidata"] == "Q47034"


def test_root_department_beats_direct_department():
    # SYNTHETIC root/direct department pair.
    _, item = operated(
        Categories.LIBRARY,
        {"root_department": "r", "department": "d", "municipality": "helsinki"},
        {"r": "Helsingin kaupunki", "d": "Espoon kaupunki"},
    )
    assert item["operator"] == "Helsingin kaupunki"


def test_pilke_and_pelastusarmeija_brands():
    # SYNTHETIC chain organizers and names.
    item = branded({"organizer_name": "Pilke päiväkodit Oy", "name": {"fi": "Pilke Playschool"}})
    assert item["brand"] == "Pilke"
    item = branded({"organizer_name": "Pelastusarmeija", "name": {"fi": "Pelastusarmeijan kirpputori"}})
    assert item["brand"] == "Pelastusarmeija"
    assert item["brand_wikidata"] == "Q120647975"


def test_website_sv_fallback_and_mailto():
    # SYNTHETIC sv website and mailto email.
    assert contacted({"www": {"sv": "https://example.fi/sv"}})["website"] == "https://example.fi/sv"
    assert contacted({"email": "mailto:info@example.fi"})["email"] == "info@example.fi"
    assert contacted({"email": "info [at] example [dot] fi"})["email"] == "info@example.fi"
    assert "email" not in contacted({"email": "info@localhost"})
    assert "phone" not in contacted({"phone": []})


def test_music_school_rescue():
    # Unit 78663 (musiikkikoulu rescue).
    spider = make_spider()
    item = Feature()
    spider._apply_name_rescue(item, {"name": {"fi": "Paavalin Musiikkikoulu"}, "service_nodes": [99999]})
    assert item.get_tag("amenity") == "music_school"


def test_florist_and_suutari_boundaries():
    # SYNTHETIC bare flower name and cobbler boundary.
    spider = make_spider()
    item = Feature()
    spider._apply_name_rescue(item, {"name": {"fi": "Kukka"}, "service_nodes": [99999]})
    assert item.get_tag("shop") == "florist"
    item = Feature()
    spider._apply_name_rescue(item, {"name": {"fi": "Suutari Korhonen"}, "service_nodes": [99999]})
    assert item.get_tag("shop") == "shoe_repair"
    item = Feature()
    spider._apply_name_rescue(item, {"name": {"fi": "Suutarila"}, "service_nodes": [99999]})
    assert item.get_tag("shop") is None


def test_genuine_island_rescue():
    # Unit 7952 (island rescue).
    spider = make_spider()
    item = Feature()
    spider._apply_name_rescue(item, {"name": {"fi": "Kotiluoto (saari)"}, "service_nodes": [548]})
    assert item.get_tag("place") == "island"


def test_generic_shop_fallback():
    # SYNTHETIC: Soma Shop shape on generic commercial nodes.
    spider = make_spider()
    item = Feature()
    spider._apply_name_rescue(item, {"name": {"fi": "Soma Shop"}, "service_nodes": [739, 750]})
    assert item.get_tag("shop") == "yes"


def test_blank_trilingual_name_dropped():
    # SYNTHETIC: no feed unit has an empty name dict.
    spider = make_spider()
    assert (
        spider._build_item(
            {
                "id": 7,
                "name": {"fi": "", "sv": "", "en": ""},
                "service_nodes": [324],
                "location": {"coordinates": [24.9, 60.1]},
            }
        )
        is None
    )
    assert spider.crawler.stats.get_value("atp/helsinki_servicemap_fi/dropped/no_name") == 1


def test_tennis_area_is_pitch_with_surface():
    # Units 79594/79578/79562 (Inkoon/Pickalan tenniskentät): bare pitch
    # row lets names supply tennis plus surface.
    item = full(make_spider(), "Pickalan tenniskentät / hiekkatekonurmikenttä 4", [662])
    assert item.get_tag("leisure") == "pitch"
    assert item.get_tag("sport") == "tennis"
    assert item["extras"]["surface"] == "artificial_turf"


def test_indoor_tennis_hall_keeps_hall():
    # Units 77133ff (Talin Tenniskeskus): co-filed halls win over courts.
    spider = make_spider({617: 614})
    item = full(spider, "Talin Tenniskeskus / Massatenniskenttä 6", [617, 662])
    assert item.get_tag("leisure") == "sports_centre"


def test_mobile_hospital_unit_keeps_hospital():
    # Unit 75620: mobile units mark their administering hospital base.
    spider = make_spider({1010: 1009})
    item = full(spider, "Lastenpsykiatrian liikkuva intensiivihoito, Töölö", [1010])
    assert item.get_tag("amenity") == "hospital"


# ---- street_address fallback review (Oct 2026): 89 fallbacks audited ----


def test_endash_housenumber_range():
    # Unit 64736: Valimotie 17–19 (U+2013).
    item = addressed(make_spider(), "Valimotie 17\u201319")
    assert item["street"] == "Valimotie"
    assert item["housenumber"] == "17-19"


def test_soft_hyphen_stripped():
    # Unit 39964 address shape.
    # Merikatu 8 + U+00AD line-break artifact.
    item = addressed(make_spider(), "Merikatu 8\u00ad")
    assert item["housenumber"] == "8"
    assert item["street"] == "Merikatu"


def test_capital_kaynti_tail_stripped():
    # Unit 70143 address shape.
    # Neilikkatie 17 - Kaynti vain ajanvarauksella: the dash-entrance
    # rule is case-insensitive (feed uses a capital K).
    item = addressed(make_spider(), "Neilikkatie 17 - K\u00e4ynti vain ajanvarauksella")
    assert item["housenumber"] == "17"
    assert item["street"] == "Neilikkatie"


def test_english_floor_tail_stripped():
    # Unit 60326 address shape.
    # Sorn\u00e4isten rantatie 33C - 4th Floor.
    item = addressed(make_spider(), "S\u00f6rn\u00e4isten rantatie 33C - 4th Floor")
    assert item["housenumber"] == "33C"


def test_spaced_courtyard_tail_stripped():
    # Unit 23234 address shape.
    # Malminkaari 23 sisapiha, Malmi (feed spells sis\u00e4piha).
    item = addressed(make_spider(), "Malminkaari 23 sis\u00e4piha, Malmi")
    assert item["housenumber"] == "23"
    assert item["street"] == "Malminkaari"


def test_numbered_middle_segment_wins():
    # SOK:n assakeskus, Fleminginkatu 34, sisapiha, Vallila
    # (feed spells ässäkeskus/sisäpiha). Unit 23213 address shape.
    item = addressed(make_spider(), "SOK:n \u00e4ss\u00e4keskus, Fleminginkatu 34, sis\u00e4piha, Vallila")
    assert item["street"] == "Fleminginkatu"
    assert item["housenumber"] == "34"


def test_kuisti_tail_with_apartment():
    # Unit 53 address shape (Kutomokuja 3 kuisti A1).
    # Kutomokuja 3 kuisti A1.
    item = addressed(make_spider(), "Kutomokuja 3 kuisti A1")
    assert item["housenumber"] == "3"
    assert item["unit"] == "A1"


def test_linja_is_bare_street():
    # Units 40626/40146: Toinen linja (no number, no other suffix).
    item = addressed(make_spider(), "Toinen linja")
    assert item["street"] == "Toinen linja"


def test_unspaced_staircase_pair():
    # Unit 60253: Lummetie 2 BC (cf. spaced "2 B C" folding to B-C).
    item = addressed(make_spider(), "Lummetie 2 BC")
    assert item["housenumber"] == "2"
    assert item["unit"] == "BC"


def test_two_letter_apartment_code():
    # Unit 64201 address shape (Minna Canthin katu 18 LH2).
    # Minna Canthin katu 18 LH2.
    item = addressed(make_spider(), "Minna Canthin katu 18 LH2")
    assert item["housenumber"] == "18"
    assert item["unit"] == "LH2"


def test_spaced_rappu_tail_is_unit():
    # SYNTHETIC: space-form staircase tail (feed uses the comma form).
    item = addressed(make_spider(), "Katu 5 A-rappu")
    assert item["housenumber"] == "5"
    assert item["unit"] == "A-rappu"


def test_station_address_stays_freeform():
    # SYNTHETIC: stations are not postal addr:place; freeform keeps them findable.
    item = addressed(make_spider(), "Kivistön asema")
    assert item["street_address"] == "Kivistön asema"
    assert "addr:place" not in item["extras"]


def test_trailing_number_reads_as_apartment():
    # Unit 22725 shape: Sibeliuksenkatu 16 8.
    item = addressed(make_spider(), "Sibeliuksenkatu 16 8")
    assert item["housenumber"] == "16"
    assert item["unit"] == "8"


def test_venue_named_addresses_stay_freeform():
    # Harbours, manors, hides, cemeteries and outdoor areas name venues.
    # Units Hietaniemen hautausmaa (54635) and Luukin ulkoilualue (50889);
    # Kotilahden satama is Unit 79743's address; rest venue-word shapes.
    # Venue-looking addresses stay freeform street_address; located_in is
    # reserved for the name-split facility-in-venue relation.
    for raw in (
        "Kotilahden satama",
        "Hakunilan kartano",
        "Fastholman lintutorni",
        "Pornaistenniemen piilokoju",
        "Hietaniemen hautausmaa",
        "Korkeasaaren eläintarha",
        "Toimelan siirtolapuutarha",
        "Uutelan niemenapaja",
        "Luukin ulkoilualue",
        "Dickursby daghem",
        "Hakunilan uimahalli",
        "Leikkipuisto Roihuvuori",
        "Tähtitornin vuori",
        "Uutelan viljelypalstat",
    ):
        item = addressed(make_spider(), raw)
        assert item["street_address"] == raw, raw
        assert "located_in" not in item, raw


def test_open_water_address_stays_freeform():
    # Seurasaaren selkä is unit 64836's address: open water is not postal
    # addr:place; freeform keeps it findable.
    item = addressed(make_spider(), "Seurasaaren selkä")
    assert item["street_address"] == "Seurasaaren selkä"
    assert "addr:place" not in item["extras"]


def test_venue_headed_address_stays_freeform():
    # Units 63023/63017: Leikkipaikka Savela (venue name first).
    item = addressed(make_spider(), "Leikkipaikka Savela")
    assert item["street_address"] == "Leikkipaikka Savela"
    assert "located_in" not in item


def test_puistikko_is_venue():
    # Unit 10934 shape: Lapinlahden puistikko stays freeform, not located_in.
    item = addressed(make_spider(), "Lapinlahden puistikko")
    assert item["street_address"] == "Lapinlahden puistikko"
    assert "located_in" not in item


def test_table_order_frozen():
    # Precedence is table order: real facilities beat parking, school beats
    # kindergarten filing. Reordering SERVICE_NODES must break this loudly.
    # Pairwise assertions (not a full snapshot): each pins a decided
    # multi-filing outcome below. SYNTHETIC combo names force the filings.
    spider = make_spider()
    order = list(spider.SERVICE_NODES)
    assert order.index(1097) < order.index(532)
    assert order.index(1097) < order.index(868)
    assert order.index(614) < order.index(662)
    assert order.index(324) < order.index(749)
    assert order.index(1004) < order.index(2189)
    assert order.index(2173) < order.index(350)
    assert order.index(155) < order.index(2173)
    assert order.index(2249) < order.index(2298)
    assert order.index(2249) < order.index(2297)
    item = full(spider, "Koulu ja pysäköinti", [1097, 532])
    assert item.get_tag("amenity") == "school"


def test_municipality_prefix_stripped_but_kept_official():
    # Unit 74116: "Lohja, Virkkalan kirjasto" repeats the city field.
    spider = make_spider()
    item = spider._build_item(
        {
            "id": 74116,
            "name": {"fi": "Lohja, Virkkalan kirjasto"},
            "service_nodes": [328, 349],
            "municipality": "lohja",
            "location": {"coordinates": [23.5, 60.25]},
        }
    )
    assert item["name"] == "Virkkalan kirjasto"
    assert item["extras"]["official_name"] == "Lohja, Virkkalan kirjasto"
    assert item["city"] == "Lohja"


def test_build_service_graph_warns_on_missing_nodes():
    # Production warning path: the tree moved under a tabled node.
    # SYNTHETIC pruned node set.
    spider = make_spider()
    spider.all_service_nodes = set(spider.SERVICE_NODES) - {1097, 868}
    spider._build_service_graph()
    assert spider.crawler.stats.get_value("atp/helsinki_servicemap_fi/tabled/missing") == 2


def test_parse_units_dedupes_identical_places():
    # Two feed records, one place: same name/coords/category collapse.
    # SYNTHETIC constructed ids 100/101.
    spider = make_spider()
    spider.seen_next = set()
    spider.expected_units = None
    spider.seen_units = 0
    unit = {
        "name": {"fi": "Kenttä"},
        "service_nodes": [659],
        "location": {"coordinates": [24.9, 60.1]},
    }
    payload = {"count": 2, "next": None, "results": [dict(unit, id=100), dict(unit, id=101)]}
    response = SimpleNamespace(
        url="https://api.hel.fi/servicemap/v2/unit/?page=1",
        headers={"Content-Type": b"application/json"},
        json=lambda: payload,
        request=SimpleNamespace(url="https://api.hel.fi/servicemap/v2/unit/?page=1", meta={}),
    )
    items = list(spider.parse_units(response))
    assert len(items) == 1
    assert spider.crawler.stats.get_value("atp/helsinki_servicemap_fi/dropped/duplicate") == 1


def test_eskola_slash_never_inverts():
    # SYNTHETIC surname guard: "Palvelu / Eskola" names the room Eskola.
    item = named(make_spider(), "Palvelu / Eskola")
    assert item["name"] == "Eskola"
    assert item["located_in"] == "Palvelu"


def test_comma_school_health_splits_service_first():
    # Unit 5664: school prefix comes out, service stays the name.
    item = full(make_spider(), "Kruununhaan yläasteen koulu, kouluterveydenhuolto", [2164, 2165])
    assert item["name"] == "kouluterveydenhuolto"
    assert item["located_in"] == "Kruununhaan yläasteen koulu"
    assert item.get_tag("healthcare") == "nurse"
    # Unit 80388: student-welfare variant at a vocational college.
    item = full(make_spider(), "Helsingin Pelastuskoulu, opiskeluterveydenhuolto", [2166, 2167])
    assert item["name"] == "opiskeluterveydenhuolto"
    assert item["located_in"] == "Helsingin Pelastuskoulu"
    assert item["extras"]["healthcare:speciality"] == "community"


def test_comma_service_health_splits_whatever_tail():
    # Units 78143/78164: service-first health names split even when the tail
    # names no school (private daycare chains), so the service is the name.
    item = full(make_spider(), "Esiopetuksen opiskeluhuolto, Touhula Fallåker", [2164, 2165])
    assert item["name"] == "Esiopetuksen opiskeluhuolto"
    assert item["located_in"] == "Touhula Fallåker"
    item = full(make_spider(), "Esiopetuksen opiskeluhuolto, Pikku Akatemia", [2164, 2165])
    assert item["name"] == "Esiopetuksen opiskeluhuolto"
    assert item["located_in"] == "Pikku Akatemia"


def test_translations_drop_fi_split_venue_tail():
    # Unit 69678: sv/en carry the same venue tail the fi split moved to
    # located_in; parity strips it there too.
    item = named(
        make_spider(),
        "Opiskeluhuolto, Karhusuon koulu",
        [2164, 2165],
        sv="Elevhälsa, Karhusuon koulu",
        en="Student welfare, Karhusuon koulu",
    )
    assert item["name"] == "Opiskeluhuolto"
    assert item["located_in"] == "Karhusuon koulu"
    assert item["extras"]["name:sv"] == "Elevhälsa"
    assert item["extras"]["name:en"] == "Student welfare"
    # Unit 64829: en water-post tail repeats the street address like fi/sv.
    item = named(
        make_spider(),
        "Vesiposti, Nupurintie 12",
        [301, 93],
        sv="Vattenpost, Nupurintie 12",
        en="Water post, Nupurintie 12",
    )
    assert item["name"] == "Vesiposti"
    assert item["extras"]["name:en"] == "Water post"


def test_ship_prefix_slash_never_splits():  # Unit 77887: en "M/S Carmel Terrace" is a ship name, not facility/venue.
    item = named(make_spider(), "Meriterassi Carmel", [2174], en="M/S Carmel Terrace")
    assert item["name"] == "Meriterassi Carmel"
    assert "located_in" not in item
    assert item["extras"]["name:en"] == "M/S Carmel Terrace"


def test_comma_facility_tail_splits_like_slash():
    # Unit 57400: comma facility tails split like their slash twins (64933).
    item = named(
        make_spider(),
        "Puistokenttä Linnaistenmetsä, lentopallokenttä",
        [658],
        sv="Park fältet Linnaisskogen, volleybollplan",
    )
    assert item["name"] == "lentopallokenttä"
    assert item["located_in"] == "Puistokenttä Linnaistenmetsä"
    assert item["extras"]["name:sv"] == "volleybollplan"
    # Unit 42382: comma-less sv tails split on the trailing court word.
    item = named(
        make_spider(),
        "Puistokenttä Kesanto, koripallokenttä",
        [657],
        sv="Park fältet Trädan Basketplan",
    )
    assert item["name"] == "koripallokenttä"
    assert item["located_in"] == "Puistokenttä Kesanto"
    assert item["extras"]["name:sv"] == "Basketplan"
    assert item["extras"]["official_name:sv"] == "Park fältet Trädan Basketplan"


def test_provider_tail_promotes_known_operator():  # Unit 74329: Puuhala runs the afternoon club; the city only files it.
    _, item = operated(
        Categories.SCHOOL,
        {"name": {"fi": "Iltapäivätoiminta / Konalan ala-asteen koulu, Puuhala Oy"}, "organizer_name": None},
    )
    assert item["operator"] == "Puuhala iltapäiväkerhot Oy"
    assert item["extras"]["operator:type"] == "private"
    # Unknown providers never promote (Beanet Oy shape): department stands.
    _, item = operated(
        Categories.SCHOOL,
        {
            "name": {"fi": "Iltapäivätoiminta / Pihlajamäen ala-aste, Beanet Oy"},
            "organizer_name": None,
            "root_department": "X",
            "municipality": "helsinki",
        },
        departments={"X": "Helsingin kaupunki"},
    )
    assert item["operator"] == "Helsingin kaupunki"
    assert "operator:type" not in item["extras"]


def test_ownership_tail_stripped_and_private():
    # Unit 64929: register flag in all three languages, never a name part.
    item = named(
        make_spider(),
        "Daghemmet Fyndet Kanel, yksityinen",
        [868],
        sv="Daghemmet Fyndet Kanel, privat",
        en="Daghemmet Fyndet Kanel, private",
    )
    assert item["name"] == "Daghemmet Fyndet Kanel"
    assert "name:sv" not in item["extras"]
    assert "name:en" not in item["extras"]
    # Organizer kept as operator, privateness flagged.
    _, item = operated(
        Categories.KINDERGARTEN,
        {"name": {"fi": "Daghemmet Fyndet Kanel, yksityinen"}, "organizer_name": "Daghemmet Kanel"},
    )
    assert item["operator"] == "Daghemmet Kanel"
    assert item["extras"]["operator:type"] == "private"
    # Unit 75921 shape: no organizer, so no city operator either.
    _, item = operated(
        Categories.SCHOOL,
        {
            "name": {"fi": "Vantaan seudun steinerkoulu, yksityinen"},
            "organizer_name": None,
            "root_department": "X",
            "municipality": "vantaa",
        },
        departments={"X": "Vantaan kaupunki"},
    )
    assert "operator" not in item
    assert item["extras"]["operator:type"] == "private"


def test_swedish_name_in_fi_field_stays_whole():
    # Unit 15413: the fi field holds a Swedish name; its nodes are untabled
    # but descend from basic education (1187 → 1097), so it files as a
    # school without splitting the Swedish name.
    parents = {1246: 1187, 1249: 1187, 1250: 1249, 1189: 1188, 1188: 1187, 1191: 1190, 1190: 1187, 1187: 1097}
    item = full(make_spider(parents), "Finno skola", [1246, 1249, 1250, 1189, 1191])
    assert item["name"] == "Finno skola"
    assert item.get_tag("amenity") == "school"


def test_translated_service_tails_stripped():  # Unit 70202: the service designation lives only in sv/en; strip it to
    # the translated venue.
    item = named(
        make_spider(),
        "Hämeenkylän koulu",
        [1374, 2350, 1375, 2164, 2165],
        sv="Hämeenkylä skola skolhälsovård",
        en="Hämeenkylä School, school health care",
    )
    assert item["name"] == "Opiskeluhuolto"
    assert item["located_in"] == "Hämeenkylän koulu"
    assert item["extras"]["name:sv"] == "Hämeenkylä skola"
    assert item["extras"]["name:en"] == "Hämeenkylä School"
    assert item["extras"]["official_name:sv"] == "Hämeenkylä skola skolhälsovård"
    assert item["extras"]["official_name:en"] == "Hämeenkylä School, school health care"
    # Bare service words stay names, never strip to nothing.
    item = named(make_spider(), "Opiskeluhuolto", [2164, 2165], en="Student welfare")
    assert item["extras"]["name:en"] == "Student welfare"


def test_translated_address_tails_stripped_like_fi():
    # Unit 74944: address tails strip from sv/en exactly like fi; the
    # structured street/housenumber (not asserted here) carries them.
    item = named(
        make_spider(),
        "Esteetön pysäköintialue Patotien päiväkoti, Patotie 8",
        [532],
        sv="Obehindrad parkeringsplats Patotien päiväkoti, Patotie 8",
        en="Unrestrained car park Patotien päiväkoti, Patotie 8",
    )
    assert item["name"] == "Esteetön pysäköintialue Patotien päiväkoti"
    assert item["extras"]["name:sv"] == "Obehindrad parkeringsplats Patotien päiväkoti"
    assert item["extras"]["name:en"] == "Unrestrained car park Patotien päiväkoti"


def test_unit_page_fan_out_math():
    # CI kill is 120s: 22 sequential pages must fan out, not next-chain.
    from types import SimpleNamespace

    spider = make_spider()
    request = SimpleNamespace(meta={})
    requests = spider._fan_unit_pages(request, {"count": 21531})
    assert len(requests) == 21
    assert spider.units_pages_pending == 22
    assert all(r.meta.get("paged") for r in requests)
    assert requests[0].url.endswith("unit/?page=2&page_size=1000&format=json")
    # Paged responses never re-fan; completion counting is once-per-page.
    assert spider._fan_unit_pages(SimpleNamespace(meta={"paged": True}), {"count": 21531}) is None
    assert spider._fan_unit_pages(SimpleNamespace(meta={}), {}) is None
    spider._count_page_done(request)
    assert spider.units_pages_pending == 21
    spider._count_page_done(request)
    assert spider.units_pages_pending == 21


def test_skating_field_is_ice_rink():
    # Unit 39819: luistelukenttä rinks are ice rinks, not pitches.
    item = full(make_spider(), "Mäkkylän luistelukenttä", [642])
    assert item.get_tag("leisure") == "ice_rink"
    assert item.get_tag("sport") == "ice_skating"


def test_hospital_departments_demoted():
    # Units filed under hospital nodes but naming wards and receptions.
    item = full(make_spider(), "Sisätautien osastot 4 ja 6, Haartmanin sairaala", [1009])
    assert item.get_tag("amenity") == "clinic"
    assert item.get_tag("healthcare") is None
    item = full(make_spider(), "Geropsykiatrian vastaanotto, Pasila", [1009])
    assert item.get_tag("amenity") == "clinic"
    # Mobile units keep the hospital; bare institution names too.
    item = full(make_spider(), "Lastenpsykiatrian liikkuva intensiivihoito, Töölö", [1009])
    assert item.get_tag("amenity") == "hospital"
    item = full(make_spider(), "Tammisairaala", [1009])
    assert item.get_tag("amenity") == "hospital"
    # Emergency departments read as urgent care (unit 70479).
    item = full(make_spider(), "Naistentautien ja synnytysten päivystys, Hyvinkään sairaala", [1009])
    assert item.get_tag("amenity") == "clinic"
    assert item.get_tag("healthcare:speciality") == "urgent"
    # Co-filed clinical rows win over the hospital row (unit 68400).
    item = full(make_spider(), "Kliininen neurofysiologia, Raaseporin sairaala", [1018, 1010])
    assert item.get_tag("healthcare") == "medical_imaging"


def test_wellness_centre_health_stations_are_clinics():
    # Units 61667/54491: genuine health centres, not eco-stores.
    item = full(make_spider(), "Myllypuron terveys- ja hyvinvointikeskus", [2190])
    assert item.get_tag("amenity") == "clinic"
    item = full(make_spider(), "Kalasataman terveys- ja hyvinvointikeskus", [2190])
    assert item.get_tag("amenity") == "clinic"
    # Ruohonjuuri stores keep the shop.
    item = full(make_spider(), "Ruohonjuuri Itis", [739, 750, 2190])
    assert item.get_tag("shop") == "health_food"


def test_swimming_pier_is_pier():
    # Unit 79589: piers filed as beaches.
    item = full(make_spider(), "Gälisnäsin uimalaituri", [688])
    assert item.get_tag("man_made") == "pier"
    item = full(make_spider(), "Vilniemen uimaranta", [688])
    assert item.get_tag("natural") == "beach"


def test_toollibrary_beats_pier_substring():
    # SYNTHETIC (no talkoolaituri filed under 688): tool libraries keep
    # their rescue category even though the noun contains "laituri".
    item = full(make_spider(), "Rantatalkoolaituri", [688])
    assert item.get_tag("amenity") == "tool_library"
    assert item.get_tag("man_made") is None


def test_football_stadium_has_soccer():
    # Unit 20999 shape: stadiums are never sportless.
    item = full(make_spider(), "Bolt Arena", [656])
    assert item.get_tag("leisure") == "pitch"
    assert item.get_tag("sport") == "soccer"


def test_staff_canteen_is_canteen():
    # Unit 77540: co-filed under generic restaurants, still a staff canteen.
    item = full(make_spider(), "Henkilöstöravintola, ravintola Merta", [183, 751])
    assert item.get_tag("amenity") == "canteen"


def test_valaistu_tail_sets_lit():
    # Unit 68639: lit trails carry the attribute, not the name.
    item = named(make_spider(), "Keimolan hiihtoharjoittelualue, valaistu", [595])
    assert item["name"] == "Keimolan hiihtoharjoittelualue"
    assert item["extras"]["lit"] == "yes"


def test_coordinate_tails_stripped_from_island_names():
    # Units 57204/57612: raw coordinates are not name parts, in any language.
    item = named(
        make_spider(),
        "Kuusiluoto, P 60° 12,239' ja I 24° 59,696'",
        [548],
        sv="Granholmen, N 60° 12,239' och E 24° 59,696'",
    )
    assert item["name"] == "Kuusiluoto"
    assert item["extras"]["name:sv"] == "Granholmen"
    assert item["extras"]["official_name"] == "Kuusiluoto, P 60° 12,239' ja I 24° 59,696'"
    item = named(make_spider(), "Lähteelän ulkoilualue N 59° 58,8' E 24° 26,3'", [548])
    assert item["name"] == "Lähteelän ulkoilualue"


def test_hosted_site_splits_to_venue():
    # Units 68526/78533: institution heads with hosted site tails.
    item = full(make_spider(), "Vantaan musiikkiopisto, Aurinkokiven koulun opetuspiste", [1370])
    assert item["name"] == "Vantaan musiikkiopisto"
    assert item["located_in"] == "Aurinkokiven koulun opetuspiste"
    item = full(make_spider(), "Stadin ammattiopisto, Nilsiänkadun toimipaikka", [2180])
    assert item["name"] == "Stadin ammattiopisto"
    assert item["located_in"] == "Nilsiänkadun toimipaikka"
    # Unit 69937: same systematic class (street-named site).
    item = full(make_spider(), "Työtehoseura, Sarkatien toimipiste", [2167, 2166])
    assert item["name"] == "Työtehoseura"
    assert item["located_in"] == "Sarkatien toimipiste"


def test_bureau_tail_stripped():  # Unit 79871: department bureaucracy is metadata, kept in official_name.
    fi = "Iltapäivätoiminta / Pasilan peruskoulu / Vaativan tuen erityisopetus, Kasvatuksen ja koulutuksen toimiala (vaativan tuen erityisopetus)"
    item = named(make_spider(), fi, [1181])
    assert item["name"] == "Iltapäivätoiminta / Pasilan peruskoulu / Vaativan tuen erityisopetus"
    assert item["extras"]["official_name"] == fi


def test_kielikylpy_descriptor_district_locates():
    # Units 20243/72753: the dash descriptor names no venue; the district does.
    item = named(make_spider(), "Länsiväylän kielikylpy, Tapiola - ruotsin kielen kielikylpypäiväkoti", [2164])
    assert item["name"] == "Länsiväylän kielikylpy"
    assert item["located_in"] == "Tapiola"
    item = named(make_spider(), "Länsiväylän kielikylpy, Olari 2 - ruotsinkielinen kielikylpypäiväkoti", [2164])
    assert item["name"] == "Länsiväylän kielikylpy"
    assert item["located_in"] == "Olari 2"


def test_ry_provider_tail_promotes_club():
    # Unit 76868: association tails strip like Oy ones and promote.
    fi = "Iltapäivätoiminta / Laajasalon peruskoulu, Helsingin Nuorten Miesten Kristillinen Yhdistys r.y."
    item = named(make_spider(), fi, [1181])
    assert item["name"] == "Iltapäivätoiminta / Laajasalon peruskoulu"
    _, item = operated(Categories.SCHOOL, {"name": {"fi": fi}, "organizer_name": None})
    assert item["operator"] == "Helsingin Nuorten Miesten Kristillinen Yhdistys r.y."
    assert item["extras"]["operator:type"] == "private"


def test_service_headed_translation_venue_skipped():  # Unit 76771: en venue slot holds the service (feed typo included).
    item = named(
        make_spider(),
        "Iltapäivätoiminta / Tahvonlahden ala-aste, Sportti Iltapäiväkerhot Oy",
        [1181],
        en="fter-school activities / Tahvonlahti Comprehensive school/ Sportti Iltapäiväkerhot Oy",
    )
    assert "located_in" not in item
    assert item["extras"]["name:en"] == "Tahvonlahti Comprehensive school"


def test_provider_infix_splits_host():
    # Unit 50608: the signed name is Terveystalo Otaniemi (Q11897034,
    # verified Finnish private healthcare company); Aalto hosts it.
    item = named(
        make_spider(),
        "Aalto-yliopisto Terveystalo Otaniemi",
        [994, 1359],
        sv="Aalto-universitetet Terveystalo Otaniemi",
        en="Aalto University Terveystalo Otaniemi",
    )
    assert item["name"] == "Terveystalo Otaniemi"
    assert item["located_in"] == "Aalto-yliopisto"
    assert "name:sv" not in item["extras"]
    assert "name:en" not in item["extras"]
    assert item["extras"]["official_name:sv"] == "Aalto-universitetet Terveystalo Otaniemi"
    assert (
        branded({"name": {"fi": "Aalto-yliopisto Terveystalo Otaniemi"}, "organizer_name": None})["brand"]
        == "Terveystalo"
    )
    assert (
        branded({"name": {"fi": "Aalto-yliopisto Terveystalo Otaniemi"}, "organizer_name": None})["brand_wikidata"]
        == "Q11897034"
    )
    _, item = operated(
        Categories.CLINIC,
        {"name": {"fi": "Aalto-yliopisto Terveystalo Otaniemi"}, "organizer_name": None},
    )
    assert item["operator"] == "Terveystalo"
    assert item["operator_wikidata"] == "Q11897034"
    assert item["extras"]["operator:type"] == "private"


def test_loading_dock_rescue():
    # Units 59265/59266: back-of-house docks are still mappable POIs.
    item = full(make_spider(), "A Bloc lastauslaituri", [514])
    assert item.get_tag("amenity") == "loading_dock"
    item = full(make_spider(), "Aalto ARTS Väre lastausalue", [1359])
    assert item.get_tag("amenity") == "loading_dock"


def test_private_contract_school_flag():
    # Unit 34961 shape: the feed's own private vocabulary.
    _, item = operated(
        Categories.SCHOOL,
        {"name": {"fi": "X"}, "organizer_name": None, "displayed_service_owner_type": "PRIVATE_CONTRACT_SCHOOL"},
    )
    assert item["extras"]["operator:type"] == "private"
    assert "operator" not in item


def test_swedish_only_name_refines():
    # SYNTHETIC Swedish-only youth-room name.
    # Swedish-only youth-room name still refines through the noun tables.
    spider = make_spider()
    item = spider._build_item(
        {
            "id": 999001,
            "name": {"sv": "Ungdomsgård Arabias"},
            "service_nodes": [2004],
            "location": {"coordinates": [24.9, 60.1]},
        }
    )
    assert item is not None


def test_tenant_gets_private_type():
    # Shops are private tenants: brand carries the name, operator:type the privateness.
    # SYNTHETIC: name avoids testi* so the test-data filter does not fire.
    spider = make_spider()
    item = spider._build_item(
        {
            "id": 999002,
            "name": {"fi": "Kauppa Kaneli"},
            "service_nodes": [739],
            "location": {"coordinates": [24.9, 60.1]},
        }
    )
    assert item is not None
    assert item["extras"].get("operator:type") == "private"


def test_cross_street_kept_whole():
    # SYNTHETIC: letter streets on both sides of the dash name no single
    # street; numbered ranges still parse.
    item = addressed(make_spider(), "Katu 5 - Katu 6")
    assert item["street_address"] == "Katu 5 - Katu 6"
    assert "housenumber" not in item


def test_parenthesised_staircase_is_unit():
    # SYNTHETIC: single-letter parens are staircases, not wings.
    item = addressed(make_spider(), "Katu 5 (A)")
    assert (item["street"], item["housenumber"], item["unit"]) == ("Katu", "5", "A")
    item = addressed(make_spider(), "Sairaalatie 8, (A)")
    assert (item["street"], item["housenumber"], item["unit"]) == ("Sairaalatie", "8", "A")


def test_provider_tail_tolerates_trailing_space():
    # SYNTHETIC: feed trailing space must not break the end anchor.
    spider = make_spider()
    assert (
        spider._provider_tail_operator({"name": {"fi": "Iltap\u00e4kerho, Puuhala Oy "}})
        == "Puuhala iltap\u00e4iv\u00e4kerhot Oy"
    )


def test_velodrome_is_track_and_spa_keeper():
    # Node 651 Pyöräilyrata is a track like 670 Karting-rata, not a pitch.
    # Unit 41334 is the Käpylä velodrome; Hilla Helsinki is unit 80697.
    item = full(make_spider(), "Velodromi", [651])
    assert item.get_tag("leisure") == "track"
    assert item.get_tag("sport") == "cycling"
    # Spa trade word falls through to its owning rule (unit: Hilla Helsinki).
    item = full(make_spider(), "Hilla Helsinki - Day Spa & Shop", [2168])
    assert item.get_tag("shop") == "beauty"


def test_generic_coverage_table_rows():
    # Node-anchored coverage for previously generic units (live unit ids).
    cases = [
        ("Shakkilauta, Hesperianpuisto", [2237, 2236], "leisure", "pitch", 73192),
        ("Saukonpaadenpuiston koirakäymälä", [495, 18, 64], "amenity", "dog_toilet", 66782),
        ("Keskuspuiston kiintorastit", [600], "leisure", "sports_centre", 64640),
        ("Metsäpirtin multa, Viikin noutomyyntipiste", [88, 296], "shop", "garden_centre", 22722),
        ("Leppävaaran pulkkamäki", [2424], "leisure", "playground", 79627),
        ("Keimolan kilpahiihtokeskus", [596], "leisure", "sports_centre", 42552),
        ("Laskettelurinne", [576], "leisure", "sports_centre", 45164),
        ("Inkoon ampumarata", [560], "leisure", "pitch", 79567),
        ("Inkoon ilma-aserata", [628], "leisure", "sports_hall", 79619),
        ("Inkoon ampumahiihtoalue", [593], "leisure", "pitch", 79608),
        ("Torbackan lentopaikka", [676], "aeroway", "aerodrome", 79561),
        ("Vanhankaupungin vesivoimalaitos", [275, 27], "power", "plant", 7210),
        ("Perheneuvola pohjoinen työryhmä", [2318], "amenity", "social_facility", 3132),
        ("Helsingin edunvalvontatoimisto, Helsingin toimipaikka", [775], "office", "government", 28931),
        ("Hekan asiakaspalvelupiste", [247, 135, 9], "office", "government", 10010),
        ("Tonttiyksikkö", [249, 137, 536, 76], "office", "government", 21975),
        ("Asemakaavoitus", [225, 331], "office", "government", 53388),
        ("Kaupunkitekniikan keskus", [2159], "office", "government", 21971),
        ("Terveydensuojelu", [104, 109, 119, 114], "office", "government", 8207),
        ("Tartuntatautien ja infektioiden torjuntayksikkö", [998], "office", "government", 69965),
        ("Rekrytointipalvelut", [124, 185], "office", "employment_agency", 64078),
        ("Seure", [124, 185], "office", "employment_agency", 9292),
        ("VillageWorks Ruoholahti", [157, 2021], "office", "property_management", 79262),
        ("Energiatori", [274, 26], "office", "consulting", 7206),
        ("Kaupunkiympäristön arkisto", [313, 331], "amenity", "archive", 57308),
        ("Ravitsemusterapia, Tikkurilan terveysasema", [1039], "healthcare", "nutrition_counselling", 71847),
        ("Oulunkylän kuntoutuskeskus sr", [1037], "healthcare", "rehabilitation", 10079),
        ("Mielenterveystyön perhehoito", [2386, 2385], "amenity", "social_facility", 6030),
        ("Malminiityn kerhotila", [404], "amenity", "community_centre", 43161),
        ("EestiMaja Viro-keskus", [355], "amenity", "community_centre", 68933),
        ("Paloheinän ulkoilumaja", [704], "amenity", "shelter", 41518),
        ("Pitäjänmäen moottorihalli", [389], "amenity", "community_centre", 8076),
        ("Nuorten liikennekoulutusalue Tattarisuo", [389, 440], "amenity", "community_centre", 8034),
        ("Musik- och kulturskolan Sandels", [2417], "amenity", "music_school", 80919),
        ("Pukinmäen sirkuskoulu", [2412, 2414, 2416, 2417], "amenity", "training", 77595),
        ("Käsityökoulu", [2401], "amenity", "training", 76961),
        ("Torra Lövö", [548], "place", "island", 22257),
        ("Porsas", [548, 71, 502], "place", "island", 50872),
    ]
    spider = make_spider()
    for fi, nodes, tag, value, ref in cases:
        assert full(spider, fi, nodes).get_tag(tag) == value, (ref, fi)


def test_generic_coverage_rescue_nouns():
    # Bare nouns on fake node 99999 isolate the rescue layer. Rows with ref
    # None are SYNTHETIC (Mallila names avoid testi*).
    cases = [
        ("Rush-trampoliinipuisto", "leisure", "trampoline_park", 53151),
        ("Seikkailupuisto Korkee", "leisure", "sports_centre", 53144),
        ("Paloheinän pulkkamäki", "leisure", "playground", 41884),
        ("Paloheinän ulkoilumaja", "amenity", "shelter", 41518),
        ("Hiihtomaja", "amenity", "shelter", 40125),
        ("Pukinmäen mopohalli", "amenity", "community_centre", None),
        ("Perheneuvola pohjoinen", "amenity", "social_facility", None),
        ("Nuorisovaltuusto", "office", "government", 20042),
        ("Helsingin kaupunginhallitus", "office", "government", 25726),
        ("Kulttuuripaja Kitee", "amenity", "community_centre", None),
        ("Kansalaistoimintakerros", "amenity", "community_centre", 45057),
        ("Yleisökassa", "amenity", "payment_centre", 8260),
        ("Helsinki Kamppi matkatavarasäilytys", "amenity", "luggage_locker", 75621),
        ("Musiikkistudio Kobra", "amenity", "studio", 75040),
        ("Lasistudio Hytti", "amenity", "arts_centre", 79711),
        ("UDUMBARA keramiikka studio", "shop", "pottery", 57095),
        ("Kontulan askartelupaja", "amenity", "arts_centre", 7992),
        ("Base Catering", "craft", "caterer", 77038),
        ("Energiatori", "office", "consulting", 7206),
        ("Puolustusvoimat, Uudenmaan aluetoimisto", "office", "government", 60154),
        ("Keski-Uudenmaan ympäristökeskus", "office", "government", 60142),
        ("Apuvälinemyymälä Aviris", "shop", "medical_supply", 34705),
        ("Sirkuskoulu Tapanila", "amenity", "training", None),
        ("Musiikkiopisto Juvenalia", "amenity", "music_school", None),
        ("Koirakäymälä Mallipuisto", "amenity", "dog_toilet", None),
        ("Voimalaitos Mallilä", "power", "plant", None),
        ("Kuntoutuskeskus Mallila", "healthcare", "rehabilitation", None),
        ("Ravitsemusterapia Mallila", "healthcare", "nutrition_counselling", None),
        ("Metsäkeskus Mallila", "office", "government", None),
        ("Exit Room Helsinki", "leisure", "escape_game", 54733),
        ("Leo's Leikkimaa Mallila", "leisure", "playground", None),
        ("CityKatsastus Mallila", "amenity", "vehicle_inspection", 68147),
        ("Pakastus Mallila", "shop", "storage_rental", None),
        ("Tukisuhdetoiminta Mallila", "amenity", "social_facility", 79223),
        ("Tiny Wonders", "amenity", "kindergarten", 78360),
        ("Silmälasistudio", "shop", "optician", 68607),
        ("Monistamo Mallila", "shop", "copyshop", None),
    ]
    spider = make_spider()
    for fi, tag, value, ref in cases:
        assert full(spider, fi, [99999]).get_tag(tag) == value, (ref, fi)


def test_generic_coverage_sport_venues():
    # Sport-carrying rescues (untabled names on fake node 99999; Mallila
    # names are SYNTHETIC and avoid testi* so the test-data filter stays quiet).
    cases = [
        ("Joogastudio Mallila", ["yoga"], 78519),
        ("Pilates Studio Mallila", ["pilates"], 79686),
        ("Ampumarata Mallila", ["shooting"], 79567),
        ("Ampumahiihto Mallila", ["biathlon"], 79608),
        ("Hiihtokeskus Mallila", ["cross_country_skiing"], 42552),
        ("Shakkilauta Mallipuisto", ["chess"], 73192),
        ("Kiintorastit Mallila", ["orienteering"], 64640),
        ("Kiipeilyhalli Mallila", ["climbing"], 78899),
        ("Padelhalli Mallila", ["padel"], None),
        ("Arena Center Mallila", ["floorball"], None),
        ("Laskettelurinne Mallila", ["skiing"], 45164),
    ]
    spider = make_spider()
    for fi, sports, ref in cases:
        assert full(spider, fi, [99999]).get_tag("sport") == ";".join(sorted(sports)), (ref, fi)


def test_island_venue_overrides():
    # SYNTHETIC: names constructed; cf. live units Klippan 57111 and Särkkä
    # 57113, whose descs confirm the restaurant villa and yacht club;
    # Tullisaari passes via the node-503 table row rather than the island branch.
    spider = make_spider()
    assert full(spider, "Suomenlinna", [548]).get_tag("tourism") == "attraction"
    assert full(spider, "Klippan", [548]).get_tag("amenity") == "restaurant"
    assert full(spider, "Särkkä", [548]).get_tag("leisure") == "marina"
    assert full(spider, "Tullisaari, viljelypalstat", [503, 73]).get_tag("landuse") == "allotments"
    assert full(spider, "Helsinki Taxi Boat", [748, 548]).get_tag("tourism") == "tours"


def test_wellness_desc_trades():
    # SYNTHETIC: hand-written descs exercising the helper directly; the
    # feed has no such description strings.
    spider = make_spider()
    assert (
        spider._wellness_desc_category(
            Categories.SAUNA, [2168], "kauneushoitola, laaja valikoima kauneushoitopalveluita"
        )
        is Categories.SHOP_BEAUTY
    )
    assert (
        spider._wellness_desc_category(Categories.SAUNA, [2168], "parturi-kampaamo, meikkaus- ja stailauspalvelut")
        is Categories.SHOP_HAIRDRESSER
    )
    assert (
        spider._wellness_desc_category(Categories.SAUNA, [2168], "joogastudio, yinjoogaa ja pilatesta")
        is Categories.GYM
    )
    assert spider._wellness_desc_category(Categories.SAUNA, [155], "kauneushoitola") is None


def test_rescue_desc_venue():
    # Description evidence for 2246-filed activity venues (descs verbatim
    # from live units Sugoi 78852, EXITE 64714, OLiO VR 79328, HELAXE 68658,
    # Fööni 57705, Takeoff 44848, Eagle Club 78988, Social Sports 78253,
    # SuperPark 53150, Laguuni 77927; unit dicts hand-built).
    spider = make_spider()

    def rescued(fi, nodes, desc):
        item = Feature()
        unit = {"name": {"fi": fi}, "service_nodes": nodes, "description": {"fi": desc}}
        assert spider._rescue_desc_venue(item, unit) is True, fi
        return item

    assert rescued("Sugoi", [2246], "pelihalli, noin 80 videopeliautomaattia").get_tag("leisure") == "amusement_arcade"
    assert rescued("EXITE Live Games", [2246], "escape room-pelikeskus").get_tag("leisure") == "escape_game"
    assert (
        rescued("OLiO VR", [2246], "VR-areena, pakohuoneet virtuaaliareenalla").get_tag("leisure") == "amusement_arcade"
    )
    item = rescued("HELAXE", [2246], "urbaani kirveenheittorata")
    assert (item.get_tag("leisure"), item.get_tag("sport")) == ("sports_centre", "axe_throwing")
    assert rescued("Fööni", [2246], "vapaalentotunneli").get_tag("leisure") == "sports_centre"
    assert (
        rescued("Takeoff Simulations", [2246], "matkustajalentokonesimulaattorielämys").get_tag("tourism")
        == "attraction"
    )
    item = rescued("Eagle Club", [2246], "TrackMan golf- ja ammuntasimulaattorit")
    assert (item.get_tag("leisure"), item.get_tag("sport")) == ("sports_centre", "golf")
    item = rescued("Social Sports Club", [2246], "pelata padelia, golfata simulaattorissa")
    assert (item.get_tag("leisure"), item.get_tag("sport")) == ("sports_hall", "padel")
    assert rescued("SuperPark Vantaa", [2246], "temppuile trampoliineilla").get_tag("leisure") == "trampoline_park"
    assert rescued("Laguuni", [2246], "vuokrattavaksi polkuveneet, SUP-laudat").get_tag("amenity") == "boat_rental"
    item = rescued(
        "Outshine Center", [2246], "tennis- ja sulkapallohalli, kolme tenniskenttää ja neljä sulkapallokenttää"
    )
    assert (item.get_tag("leisure"), item.get_tag("sport")) == ("sports_hall", "badminton;tennis")
    assert rescued("Muikku Photo", [2246], "vintage-henkinen photobooth ja luova studio").get_tag("amenity") == "studio"
    # Gate: other nodes never fire, empty descs never fire (SYNTHETIC units).
    item = Feature()
    assert (
        spider._rescue_desc_venue(
            item, {"name": {"fi": "Sugoi"}, "service_nodes": [99999], "description": {"fi": "pelihalli"}}
        )
        is False
    )
    item = Feature()
    assert (
        spider._rescue_desc_venue(item, {"name": {"fi": "Sugoi"}, "service_nodes": [2246], "description": {"fi": ""}})
        is False
    )
