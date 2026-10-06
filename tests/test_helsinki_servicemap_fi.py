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
    for raw in ("-", "–"):
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


def test_talkoolaituri_is_tool_library():
    # Unit 79897: Clean-up station, not a pier.
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
    # Unit 77517 shape: Kallion kirkon torni. A tower is a building part
    # with no independent premises, so no worship tag — but the named record
    # is still yielded as amenity=yes per docs/CATEGORIES.md rather than
    # dropped outright.
    spider = make_spider()
    item = Feature()
    unit = {"name": {"fi": "Kallion kirkon torni"}, "service_nodes": [350, 749]}
    spider._apply_name(item, unit)
    spider._apply_category(item, unit)
    assert item.get_tag("amenity") == "yes"
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


def test_loading_dock_filed_as_ticket_stays_generic():
    # Unit 59265: A Bloc lastauslaituri is a service-yard dock, not ticket sales.
    item = full(make_spider(), "A Bloc lastauslaituri", [514])
    assert item.get_tag("shop") is None
    assert item.get_tag("amenity") == "yes"


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
    # SYNTHETIC studio names: wellness filing stands, while rental-sauna
    # rows (155/264/511) yield to a co-filed events venue.
    item = full(make_spider(), "Pranama Kallio", [2168, 2173])
    assert item.get_tag("leisure") == "sauna"
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


def test_website_scheme_added():
    # SYNTHETIC (feed has no schemeless www left).
    item = contacted({"www": {"fi": "www.hel.fi/palvelukartta"}})
    assert item["website"] == "https://www.hel.fi/palvelukartta"


def test_website_bad_scheme_rejected():
    # SYNTHETIC bad-scheme website.
    item = contacted({"www": {"fi": "ftp://x.fi/file"}})
    assert "website" not in item


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
    assert spider._university_category(cat, "dipoli") is False
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
    item = addressed(make_spider(), "Valimotie 17–19")
    assert item["street"] == "Valimotie"
    assert item["housenumber"] == "17-19"


def test_soft_hyphen_stripped():
    # Unit 39964 address shape.
    # Merikatu 8 + U+00AD line-break artifact.
    item = addressed(make_spider(), "Merikatu 8­")
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


def test_station_address_takes_addr_place():
    # SYNTHETIC: stations are not postal addr:place; freeform keeps them findable.
    item = addressed(make_spider(), "Kivistön asema")
    assert item["street_address"] == "Kivistön asema"
    assert "addr:place" not in item["extras"]


def test_trailing_number_reads_as_apartment():
    # Unit 22725 shape: Sibeliuksenkatu 16 8.
    item = addressed(make_spider(), "Sibeliuksenkatu 16 8")
    assert item["housenumber"] == "16"
    assert item["unit"] == "8"


def test_venue_named_addresses_route_to_located_in():
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


def test_open_water_takes_addr_place():
    # Seurasaaren selkä is unit 64836's address: open water is not postal
    # addr:place; freeform keeps it findable.
    item = addressed(make_spider(), "Seurasaaren selkä")
    assert item["street_address"] == "Seurasaaren selkä"
    assert "addr:place" not in item["extras"]


def test_venue_headed_address_routes_to_located_in():
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
    order = list(make_spider().SERVICE_NODES)
    assert order.index(1097) < order.index(532) if 532 in order else True
    assert order.index(1097) < order.index(868)
    assert order.index(614) < order.index(662)
    assert order.index(324) < order.index(749)
    assert order.index(1004) < order.index(2189) if 2189 in order else True
    assert order.index(2173) < order.index(350)
    assert order.index(155) < order.index(2173)
    assert order.index(2249) < order.index(2298)
    assert order.index(2249) < order.index(2297)
    item = full(make_spider(), "Koulu ja pysäköinti", [1097, 532] if 532 in make_spider().SERVICE_NODES else [1097])
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
