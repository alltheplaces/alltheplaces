# -*- coding: utf-8 -*-
"""Behavioural tests for ptv_fi.

Each case pins a load-bearing rule: name splits, branch handling, address
parsing, category precedence/refinement and operator/contact attribution.
Cases use real PTV feed shapes (mirror sample or full-crawl records) unless
marked SYNTHETIC, in which case the input exercises a helper branch
directly. Helpers (split, named, addressed, categorised) test one method in
isolation; parsed() runs the full parse_channel path.
"""

from types import SimpleNamespace

from locations.categories import Categories
from locations.items import Feature
from locations.spiders.government.ptv_fi import PtvFISpider


class _Stats:
    def __init__(self):
        self.d = {}

    def inc_value(self, key, n=1):
        self.d[key] = self.d.get(key, 0) + n

    def get_value(self, key, default=0):
        return self.d.get(key, default)


def make_spider():
    spider = PtvFISpider()
    spider.crawler = SimpleNamespace(stats=_Stats())
    return spider


def split(spider, fi, city=None):
    return spider._split_name(fi, city)


def named(spider, fi, city=None):
    # Clean-then-split composition, as parse_channel applies it.
    return spider._split_name(spider._clean_name(fi), city)


def cat(spider, fi):
    return spider._category(fi)


def addressed(spider, road, number, postcode="00100", office="HELSINKI"):
    item = Feature()
    street = {"street": [{"language": "fi", "value": road}], "streetNumber": number}
    spider._apply_address(item, street, postcode, spider._post_city(office))
    return item


def channel(
    fi,
    street_number="1",
    road="Katu",
    postcode="00100",
    office="HELSINKI",
    org="org-1",
    sv=None,
    en=None,
    hours=None,
    descriptions=None,
):
    names = [{"language": "fi", "value": fi}]
    if sv is not None:
        names.append({"language": "sv", "value": sv})
    if en is not None:
        names.append({"language": "en", "value": en})
    data = {
        "id": "11111111-1111-4111-8111-111111111111",
        "serviceChannelType": "ServiceLocation",
        "publishingStatus": "Published",
        "organizationId": org,
        "serviceChannelNames": names,
        "addresses": [
            {
                "type": "Location",
                "subType": "Single",
                "streetAddress": {
                    "street": [{"language": "fi", "value": road}],
                    "streetNumber": street_number,
                    "postalCode": postcode,
                    "postOffice": [{"language": "fi", "value": office}],
                    "latitude": "6672010",
                    "longitude": "385128",
                    "coordinateState": "Ok",
                },
            }
        ],
        "serviceHours": hours or [],
        "phoneNumbers": [],
        "emails": [],
        "webPages": [],
    }
    if descriptions is not None:
        data["serviceChannelDescriptions"] = descriptions
    return data


def parsed(spider, data, org_name=None):
    item = spider.parse_channel(data)
    assert item is not None
    spider._apply_operator(item, org_name)
    return item


# ---- Quadrant A: name splitting, cleaning and branches ---------------------

# Quadrants mirror the spider's pipeline sections: A names/branches,
# B addresses, C categories, D operator/contact/hours. Helper-level cases
# pin one method; parsed() runs the full parse_channel path.


def test_machine_splits_head_with_official():
    # Pysäköintilippuautomaatti 222 shape: address + payment metadata.
    name, located, official = named(make_spider(), "Pysäköintilippuautomaatti 222, Pengerkatu 23, korttimaksu")
    assert name == "Pysäköintilippuautomaatti 222"
    assert located is None
    assert official == "Pysäköintilippuautomaatti 222, Pengerkatu 23, korttimaksu"


def test_machine_with_slash_location_note():
    # Mäntymäenkenttä / 2 location note must not mis-split.
    name, located, official = named(make_spider(), "Pysäköintilippuautomaatti 619, Mäntymäenkenttä / 2, korttimaksu")
    assert name == "Pysäköintilippuautomaatti 619"
    assert located is None
    assert official is not None


def test_machine_without_tails_stays_whole():
    assert split(make_spider(), "Pysäköintilippuautomaatti 591") == (
        "Pysäköintilippuautomaatti 591",
        None,
        None,
    )


def test_paren_venue_names_base():
    # Host venue buried in trailing parens.
    name, located, official = split(make_spider(), "Luustoyhdistyksen vesijumppa Helsingissä (Oltermannikeskus)")
    assert name == "Luustoyhdistyksen vesijumppa Helsingissä"
    assert located == "Oltermannikeskus"
    assert official is not None


def test_paren_address_stripped_to_base():
    assert split(make_spider(), "Mäntymäen päiväkoti (Kallelankatu 3)")[0] == "Mäntymäen päiväkoti"
    assert split(make_spider(), "Totto-Halli (Muurola)")[0] == "Totto-Halli"


def test_paren_operator_head_keeps_venue():
    # Pilke päiväkodit Oy/ Musiikkipäiväkoti Sinikello (Tuureporinkatu 5 E).
    name, located, official = named(
        make_spider(), "Pilke päiväkodit Oy/ Musiikkipäiväkoti Sinikello (Tuureporinkatu 5 E)"
    )
    assert name == "Musiikkipäiväkoti Sinikello"
    assert located is None
    assert official is not None


def test_dash_unit_splits_venue():
    # Friemanin talo - nuorisotoimisto.
    name, located, official = split(make_spider(), "Friemanin talo - nuorisotoimisto")
    assert name == "Nuorisotoimisto"
    assert located == "Friemanin talo"
    assert official is not None


def test_dash_without_unit_stays_whole():
    spider = make_spider()
    assert split(spider, "Malminkartano - Pitäjänmäki")[1] is None


def test_acronym_prefix_venue():
    # OYSin Keuhkosairauksien poliklinikka.
    name, located, official = split(make_spider(), "OYSin Keuhkosairauksien poliklinikka")
    assert name == "Keuhkosairauksien poliklinikka"
    assert located == "OYS"
    assert official is not None


def test_slash_room_names_facility():
    # Santahaminan ala-asteen koulu / Koripallokenttä.
    name, located, official = split(make_spider(), "Santahaminan ala-asteen koulu / Koripallokenttä")
    assert name == "Koripallokenttä"
    assert located == "Santahaminan ala-asteen koulu"
    assert official is not None


def test_slash_generic_room_names_facility():
    # Meilahden yläasteen koulu / Juhlasali.
    name, located, _ = split(make_spider(), "Meilahden yläasteen koulu / Juhlasali")
    assert name == "Juhlasali"
    assert located == "Meilahden yläasteen koulu"


def test_slash_numbered_room_keeps_context():
    # Kaarelankenttä / Hiekkakenttä 2.
    name, located, _ = split(make_spider(), "Kaarelankenttä / Hiekkakenttä 2")
    assert name == "Hiekkakenttä 2"
    assert located == "Kaarelankenttä"


def test_slash_proper_facility():
    # Sipoon lukio / Sipoon Enter.
    name, located, _ = split(make_spider(), "Sipoon lukio / Sipoon Enter")
    assert name == "Sipoon Enter"
    assert located == "Sipoon lukio"


def test_slash_institution_tail_is_venue():
    # Iltapäivätoiminta / Steiner-koulu (operator tail inside venue).
    name, located, official = split(
        make_spider(),
        "Iltapäivätoiminta / Steiner-koulu, Helsingin Rudolf Steiner-koulun kannatusyhdistys - Underst..",
    )
    assert name == "Iltapäivätoiminta"
    assert located == "Steiner-koulu"
    assert official is not None


def test_slash_institution_comma_descriptor():
    # ... / Kulosaaren ala-aste, Liikkis resolves to the school, and the
    # person segment peels first (Sari Wicklund is a contact, not a venue).
    name, located, official = split(make_spider(), "Iltapäivätoiminta / Kulosaaren ala-aste, Liikkis / Sari Wicklund")
    assert name == "Iltapäivätoiminta"
    assert located == "Kulosaaren ala-aste"
    assert official is not None


def test_slash_person_dropped():
    # SYNTHETIC contact-person tail.
    name, located, official = split(make_spider(), "Jumppa / Sari Wicklund")
    assert name == "Jumppa"
    assert located is None
    assert official is not None


def test_slash_person_sharing_school_token_kept():
    # Host-named units share a token with their school (Sipoon Enter):
    # the person guard must not eat them (covered end to end below).
    spider = make_spider()
    assert spider._is_person("Sari Wicklund") is True
    name, located, _ = split(spider, "Sipoon lukio / Sipoon Enter")
    assert (name, located) == ("Sipoon Enter", "Sipoon lukio")


def test_slash_district_head_names_facility():
    # Pohjois-Espoon / Niipperin matonpesupaikka.
    name, located, _ = split(make_spider(), "Pohjois-Espoon / Niipperin matonpesupaikka")
    assert name == "Niipperin matonpesupaikka"
    assert located is None


def test_slash_place_head_flips_to_facility():
    # Uimastadion / Pöytätennisalue.
    name, located, _ = split(make_spider(), "Uimastadion / Pöytätennisalue")
    assert name == "Pöytätennisalue"
    assert located == "Uimastadion"


def test_slash_service_tail_names_service():
    # SYNTHETIC Perhekeskus / Neuvola shape.
    name, located, _ = split(make_spider(), "Perhekeskus Pohjatuuli / Lasten neuvola")
    assert name == "Lasten neuvola"
    assert located == "Perhekeskus Pohjatuuli"


def test_slash_nested_chain():
    # Talin puttirata / Mini-Tali / Frisbeegolfin harjoittelualue.
    name, located, _ = split(make_spider(), "Talin puttirata / Mini-Tali / Frisbeegolfin harjoittelualue")
    assert name == "Mini-Tali"
    assert located == "Talin puttirata"


def test_slash_operator_head():
    # Harjulan Setlementti ry/Liikuntapalvelut -palvelun järjestämispaikka.
    name, located, official = named(
        make_spider(), "Harjulan Setlementti ry/Liikuntapalvelut -palvelun järjestämispaikka"
    )
    assert name == "Harjulan Setlementti ry"
    assert located is None
    assert official is not None


def test_slash_operator_tail_stripped_from_venue():
    # Imatra Bowling Center / Imatran keilahalli Oy: the Oy suffix strips
    # to the venue part.
    name, located, official = split(make_spider(), "Imatra Bowling Center / Imatran keilahalli Oy")
    assert name == "Imatra Bowling Center"
    assert located == "Imatran keilahalli"
    assert official is not None


def test_slash_appositive_twins():
    # Linnanlaituri / Vesiliikennelaituri: the head already names it.
    name, located, _ = split(make_spider(), "Linnanlaituri / Vesiliikennelaituri")
    assert name == "Linnanlaituri"
    assert located is None


def test_slash_memorial_stays_whole():
    # SYNTHETIC single memorial object: the peel drops the dedication tail,
    # leaving the artwork title as the name (cf. service-map Lähde).
    assert split(make_spider(), "Lähde / UKK-muistomerkki") == ("Lähde", None, "Lähde / UKK-muistomerkki")


def test_bare_slash_compounds_stay_whole():
    # SYNTHETIC Geo/on shape and hyphen fragments.
    spider = make_spider()
    assert split(spider, "koripallo/lentopallo") == ("koripallo/lentopallo", None, None)
    assert split(spider, "hiekka-/jääkenttä") == ("hiekka-/jääkenttä", None, None)


def test_bare_slash_area_drops_to_head():
    # Kotihoito/Vuosaari 3 lähipalvelualue.
    name, located, official = split(make_spider(), "Kotihoito/Vuosaari 3 lähipalvelualue")
    assert name == "Kotihoito"
    assert located is None
    assert official is not None


def test_comma_service_venue():
    # Opiskeluhuolto, Karhusuon koulu.
    name, located, _ = split(make_spider(), "Opiskeluhuolto, Karhusuon koulu")
    assert name == "Opiskeluhuolto"
    assert located == "Karhusuon koulu"


def test_comma_service_genitive():
    # Rovastinkankaan koulun opiskeluhuolto, Orivesi.
    name, located, official = split(make_spider(), "Rovastinkankaan koulun opiskeluhuolto, Orivesi", "Orivesi")
    assert name == "Opiskeluhuolto"
    assert located == "Rovastinkankaan koulu"
    assert official is not None


def test_comma_genitive_without_mappable_school_strips_city():
    # Ammattiopisto Spesian opiskeluhuolto, Salo: Spesian is a proper-noun
    # genitive with no nominative map, so only the city tail strips.
    name, located, official = split(make_spider(), "Ammattiopisto Spesian opiskeluhuolto, Salo", "Salo")
    assert name == "Ammattiopisto Spesian opiskeluhuolto"
    assert located is None
    assert official is not None


def test_comma_city_strips():
    # Kiikoisten lähitori, Sastamala.
    name, located, official = split(make_spider(), "Kiikoisten lähitori, Sastamala", "Sastamala")
    assert name == "Kiikoisten lähitori"
    assert located is None
    assert official is not None


def test_comma_city_mismatch_keeps_whole():
    name, located, official = split(make_spider(), "Mäntymäen perhetukikeskus, Turku", "Helsinki")
    assert (name, located, official) == ("Mäntymäen perhetukikeskus, Turku", None, None)


def test_comma_city_head_names_tail():
    # Vaasa, Ulosottolaitos.
    name, located, official = split(make_spider(), "Vaasa, Ulosottolaitos", "Vaasa")
    assert name == "Ulosottolaitos"
    assert located is None
    assert official is not None


def test_comma_service_unit_split():
    # Lasten puheterapia, Perhekeskus Pohjatuuli.
    name, located, _ = split(make_spider(), "Lasten puheterapia, Perhekeskus Pohjatuuli")
    assert name == "Lasten puheterapia"
    assert located == "Perhekeskus Pohjatuuli"


def test_comma_unit_venue_split():
    # Myllypuron seniorikeskus, ryhmäkoti Sonaatti.
    name, located, _ = split(make_spider(), "Myllypuron seniorikeskus, ryhmäkoti Sonaatti")
    assert name == "Ryhmäkoti Sonaatti"
    assert located == "Myllypuron seniorikeskus"


def test_comma_school_service_tail_inverts():
    # Eurooppalainen koulu European Schooling Helsinki, kouluterveydenhuolto.
    name, located, _ = split(make_spider(), "Eurooppalainen koulu European Schooling Helsinki, kouluterveydenhuolto")
    assert name == "Kouluterveydenhuolto"
    assert located == "Eurooppalainen koulu European Schooling Helsinki"


def test_comma_institution_unit_split():
    # Tehostetun avohoidon yksikkö, Lohjan sairaala.
    name, located, _ = split(make_spider(), "Tehostetun avohoidon yksikkö, Lohjan sairaala")
    assert name == "Tehostetun avohoidon yksikkö"
    assert located == "Lohjan sairaala"


def test_comma_canteen_split():
    # Kouluravintola, Pihlajamäen ala-asteen koulu.
    name, located, _ = split(make_spider(), "Kouluravintola, Pihlajamäen ala-asteen koulu")
    assert name == "Kouluravintola"
    assert located == "Pihlajamäen ala-asteen koulu"


def test_comma_acronym_venue():
    # Nuorisopsykiatrian osasto J1, Tyks.
    name, located, _ = split(make_spider(), "Nuorisopsykiatrian osasto J1, Tyks")
    assert name == "Nuorisopsykiatrian osasto J1"
    assert located == "Tyks"


def test_comma_coverage_dropped():
    # Kotihoito, Oulainen ja Merijärvi.
    name, located, official = split(make_spider(), "Kotihoito, Oulainen ja Merijärvi")
    assert name == "Kotihoito"
    assert located is None
    assert official is not None


def test_comma_dept_number_dropped():
    # Katriinan toimipiste, osasto 5.
    name, located, official = split(make_spider(), "Katriinan toimipiste, osasto 5")
    assert name == "Katriinan toimipiste"
    assert located is None
    assert official is not None


def test_comma_descriptor_peeled():
    # Attendo Ukko-Pekka, Humppila, yhteisöllisen asumisen ostopalvelut.
    name, located, official = split(make_spider(), "Attendo Ukko-Pekka, Humppila, yhteisöllisen asumisen ostopalvelut")
    assert name == "Attendo Ukko-Pekka, Humppila"
    assert located is None
    assert official is not None


def test_comma_branch_office_stays_whole():
    # Pohjanmaan elinvoimakeskus, Kokkolan toimipaikka: the campus/desk
    # qualifier is part of the signed name, never stripped (cf. Stadin
    # ammattiopisto way/1094085495); branch=* is chain-retail, not schools.
    name, located, official = split(make_spider(), "Pohjanmaan elinvoimakeskus, Kokkolan toimipaikka")
    assert (name, located, official) == (
        "Pohjanmaan elinvoimakeskus, Kokkolan toimipaikka",
        None,
        None,
    )


def test_campus_tail_stays_whole_end_to_end():
    # Stadin ammattiopisto, Roihupellon toimipaikka: full form is the name,
    # no branch, no official_name (nothing parsed off).
    spider = make_spider()
    item = parsed(spider, channel("Stadin ammattiopisto, Roihupellon toimipaikka"), "Helsingin kaupunki")
    assert item["name"] == "Stadin ammattiopisto, Roihupellon toimipaikka"
    assert item.get("branch") is None
    assert item["extras"].get("official_name") is None


def test_comma_address_dropped():
    # Koskelan ala-asteen koulu, Mäkelänkatu 84 shape.
    name, located, official = split(make_spider(), "Koskelan ala-asteen koulu, Mäkelänkatu 84")
    assert name == "Koskelan ala-asteen koulu"
    assert located is None
    assert official is not None


def test_comma_proper_venue_single_token():
    # SYNTHETIC Neuvonta, Reimasali shape (fixture tail as venue).
    name, located, _ = split(make_spider(), "Neuvonta, Reimasali")
    assert name == "Neuvonta"
    assert located == "Reimasali"


def test_comma_unit_proper_institution_head():
    # SYNTHETIC Sipoon lukio, Enter shape.
    name, located, _ = split(make_spider(), "Sipoon lukio, Enter")
    assert name == "Enter"
    assert located == "Sipoon lukio"


def test_kela_suffix_cleaned_and_detected():
    # Kokemäen Asiointipiste/Kela.
    spider = make_spider()
    assert spider._clean_name("Kokemäen Asiointipiste/Kela") == "Kokemäen Asiointipiste"
    assert spider._branch_agency("Kokemäen Asiointipiste/Kela") == "Kela"
    assert spider._branch_agency("Tavallinen nimi") is None


def test_clean_bureau_tails():
    spider = make_spider()
    assert (
        spider._clean_name("Iltapäivätoiminta / Koulu, Kasvatuksen ja koulutuksen toimiala")
        == "Iltapäivätoiminta / Koulu"
    )
    assert spider._clean_name("Nimi, Education Division") == "Nimi"


def test_clean_boilerplate_and_org_prefix():
    spider = make_spider()
    assert spider._clean_name("Jorvin Terassikahvio -palvelun järjestämispaikka") == "Jorvin Terassikahvio"
    assert spider._clean_name("Nuortenillat-palvelun järjestämispaikka") == "Nuortenillat"
    assert spider._clean_name("International House Salo, palvelupaikka") == "International House Salo"
    assert spider._clean_name("Emy ry:n Hyvän mielen ryhmä") == "Hyvän mielen ryhmä"
    assert spider._clean_name("Walonkulman Klubitalo - yhteisö työikäisille") == "Walonkulman Klubitalo"


def test_genitive_school_mapping():
    spider = make_spider()
    assert spider._genitive_school("Rovastinkankaan koulun opiskeluhuolto") == "Rovastinkankaan koulu"
    assert spider._genitive_school("Vammalan lukion opiskeluhuolto") == "Vammalan lukio"
    assert spider._genitive_school("Ammattiopisto Spesian opiskeluhuolto") is None
    assert spider._genitive_school("Opiskeluhuolto") is None


def test_post_city_station_suffix():
    spider = make_spider()
    assert spider._post_city("ORIVESI AS") == "ORIVESI"
    assert spider._post_city("ESPOO") == "ESPOO"
    assert spider._post_city(None) is None
    assert spider._post_city("  ") is None


def test_clean_located_strips_operator_city_person():
    spider = make_spider()
    assert spider._clean_located("Imatran keilahalli Oy") == "Imatran keilahalli"
    assert spider._clean_located("Sari Wicklund") is None
    assert spider._clean_located("Infopiste") is None
    assert spider._clean_located("Töölön kisahalli") == "Töölön kisahalli"


def test_is_proper_tail_guards():
    spider = make_spider()
    assert spider._is_proper_tail("Sipoon Enter") is True
    assert spider._is_proper_tail("Pöytätennisalue") is False
    assert spider._is_proper_tail("Hiekkakenttä 2") is False
    assert spider._is_proper_tail("Imatran keilahalli Oy") is False
    assert spider._is_proper_tail("Virtain toimipiste") is False


# ---- Quadrant B: address parsing -------------------------------------------


def test_staircase_unit_split():
    # Lummetie 2B, A rappu shape.
    item = addressed(make_spider(), "Lummetie", "2B, A rappu")
    assert (item["street"], item["housenumber"]) == ("Lummetie", "2b")
    assert "street_address" not in item
    assert item["extras"]["addr:unit"] == "A rappu"


def test_attached_letter_lowercased():
    item = addressed(make_spider(), "Katu", "3A")
    assert (item["street"], item["housenumber"]) == ("Katu", "3a")
    assert "street_address" not in item
    assert "addr:unit" not in item["extras"]


def test_floor_tail_parsed_not_level():
    # Kielotie 7 A, 2.kerros: the floor survives as addr:floor, never level.
    item = addressed(make_spider(), "Kielotie", "7 A, 2.kerros")
    assert (item["street"], item["housenumber"]) == ("Kielotie", "7")
    assert "street_address" not in item
    assert item["extras"]["addr:unit"] == "A"
    assert item["extras"]["addr:floor"] == "2"
    assert "level" not in item["extras"]


def test_pobox_tail_dropped():
    # Kolpintie 7, PL 111 shape.
    item = addressed(make_spider(), "Kolpintie", "7, PL 111")
    assert (item["street"], item["housenumber"]) == ("Kolpintie", "7")
    assert "street_address" not in item
    assert "addr:unit" not in item["extras"]


def test_venue_slash_tail_dropped():
    # 14 / Espoon Keskuspuisto shape.
    item = addressed(make_spider(), "Tie", "14 / Espoon Keskuspuisto")
    assert (item["street"], item["housenumber"]) == ("Tie", "14")


def test_district_tail_dropped():
    # 70, Töölö shape.
    item = addressed(make_spider(), "Tie", "70, Töölö")
    assert (item["street"], item["housenumber"]) == ("Tie", "70")


def test_building_tail_kept_as_unit():
    # Kunnallissairaalantie 20, rakennus 7 shape.
    item = addressed(make_spider(), "Kunnallissairaalantie", "20, rakennus 7")
    assert (item["street"], item["housenumber"]) == ("Kunnallissairaalantie", "20")
    assert "street_address" not in item
    assert item["extras"]["addr:unit"] == "rakennus 7"


def test_door_tail_kept_as_unit():
    # 2, A-ovi, 2. krs shape.
    item = addressed(make_spider(), "Tie", "2, A-ovi, 2. krs")
    assert (item["street"], item["housenumber"]) == ("Tie", "2")
    assert "street_address" not in item
    assert item["extras"]["addr:unit"] == "A-ovi"
    assert item["extras"]["addr:floor"] == "2"


def test_zero_number_means_numberless():
    # Hallintoaukio 0: squares carry no housenumber and route to addr:place.
    item = addressed(make_spider(), "Hallintoaukio", "0")
    assert item["extras"]["addr:place"] == "Hallintoaukio"
    assert "street_address" not in item


def test_cross_streets_stay_freeform():
    # Veräjäpellonkatu / Kaivoskallionpolku: no single postal address.
    item = addressed(make_spider(), "Veräjäpellonkatu / Kaivoskallionpolku", "")
    assert item["street_address"] == "Veräjäpellonkatu / Kaivoskallionpolku"


def test_numberless_place_goes_to_addr_place():
    # SYNTHETIC island address without a number.
    item = addressed(make_spider(), "Tiirakari", "")
    assert item["extras"]["addr:place"] == "Tiirakari"
    assert "street_address" not in item


def test_bare_street_without_number():
    item = addressed(make_spider(), "Urho Kekkosen katu", "")
    assert item["street"] == "Urho Kekkosen katu"
    assert "housenumber" not in item
    assert "street_address" not in item


def test_postcode_city_and_country_pins():
    item = addressed(make_spider(), "Katu", "1", postcode="00100", office="ESPOO")
    assert item["postcode"] == "00100"
    assert item["city"] == "Espoo"
    assert item["country"] == "FI"


def test_station_post_office_files_under_municipality():
    item = addressed(make_spider(), "Katu", "1", office="ORIVESI AS")
    assert item["city"] == "Orivesi"


def test_fused_staircase_apartment():
    # Arabianpolku 1A2 shape.
    item = addressed(make_spider(), "Arabianpolku", "1A2")
    assert (item["street"], item["housenumber"]) == ("Arabianpolku", "1a")
    assert "street_address" not in item
    assert item["extras"]["addr:unit"] == "2"


def test_spaced_housenumber_range():
    # Nummentie 12 - 14 shape.
    item = addressed(make_spider(), "Nummentie", "12 - 14")
    assert (item["street"], item["housenumber"]) == ("Nummentie", "12-14")


def test_apartment_before_stair():
    # Pursimiehenkatu 8 52 A shape.
    item = addressed(make_spider(), "Pursimiehenkatu", "8 52 A")
    assert (item["street"], item["housenumber"]) == ("Pursimiehenkatu", "8")
    assert "street_address" not in item
    assert item["extras"]["addr:unit"] == "52 A"


def test_spaced_letter_staircase():
    # 5 A shape: the letter is the staircase, never joined.
    item = addressed(make_spider(), "Katu", "5 A")
    assert (item["street"], item["housenumber"]) == ("Katu", "5")
    assert "street_address" not in item
    assert item["extras"]["addr:unit"] == "A"


# ---- Quadrant C: category mapping ------------------------------------------


def test_police_outranks_on_call():
    # Rauman poliisiasema, poliisipäivystys: police, never urgent clinic.
    category, _ = cat(make_spider(), "Rauman poliisiasema, poliisipäivystys")
    assert category == Categories.POLICE


def test_social_on_call_outranks_clinic():
    # Sosiaali- ja kriisipäivystys.
    category, _ = cat(make_spider(), "Sosiaali- ja kriisipäivystys")
    assert category == Categories.SOCIAL_FACILITY


def test_plain_on_call_stays_urgent():
    category, _ = cat(make_spider(), "Päivystys")
    assert category == Categories.CLINIC_URGENT


def test_dental_outranks_on_call():
    # Forssan hammashoidon arkipäivystys (genitive gradation included).
    category, _ = cat(make_spider(), "Forssan hammashoidon arkipäivystys")
    assert category == Categories.DENTIST


def test_school_hosted_sports_file_as_sports():
    spider = make_spider()
    for fi, category in (
        ("Saunalahden koulun hiekkakenttä", Categories.LEISURE_PITCH),
        ("Kaasmarkun koulun kaukalo", Categories.LEISURE_ICE_RINK),
        ("Kuusikon koulun luistelukenttä", Categories.LEISURE_ICE_RINK),
        ("Lietsalan koulun liikuntasali", Categories.LEISURE_SPORTS_HALL),
        ("Tiedonpuiston koulun liikuntatilat", Categories.LEISURE_SPORTS_HALL),
        ("Opinmäen koulun liikuntahalli", Categories.LEISURE_SPORTS_CENTRE),
        ("Uittamon koulun sali", Categories.LEISURE_SPORTS_HALL),
        ("Hirvaskosken koulun frisbeegolfrata", Categories.LEISURE_DISC_GOLF_COURSE),
        ("Nurmikenttä 1", Categories.LEISURE_PITCH),
    ):
        assert cat(spider, fi)[0] == category, fi


def test_school_hosted_health_files_as_health():
    spider = make_spider()
    for fi, category in (
        ("Opiskeluhuolto", Categories.CLINIC),
        ("Kouluterveydenhuolto", Categories.CLINIC),
        ("Seminaarikoulun hammashoitola", Categories.DENTIST),
        ("Pihlajamäen neuvola", Categories.CLINIC),
    ):
        assert cat(spider, fi)[0] == category, fi
    # Nurse-led: the healthcare extra survives alongside the clinic.
    assert cat(spider, "Opiskeluhuolto")[1] == {"healthcare": "nurse"}


def test_school_kitchen_unit_files_as_canteen():
    # Kouluravintola, Pihlajamäen ala-asteen koulu.
    category, _ = cat(make_spider(), "Kouluravintola, Pihlajamäen ala-asteen koulu")
    assert category == Categories.CANTEEN


def test_tori_guard_and_square_default():
    spider = make_spider()
    assert cat(spider, "Messukylän lähitori, Tampere")[0] == Categories.SOCIAL_FACILITY
    assert cat(spider, "Messilän Pääkonttori")[0] == Categories.OFFICE_COMPANY
    assert cat(spider, "Koulukuraattori")[0] == Categories.SCHOOL
    assert cat(spider, "Kiuruveden tori")[0] is None  # place=square via extras
    assert cat(spider, "Töölöntori")[1] == {"place": "square"}
    assert cat(spider, "Senaatintori")[1] == {"place": "square"}
    assert cat(spider, "Kauppatori")[0] == Categories.MARKETPLACE


def test_kirkko_compound_end_only():
    spider = make_spider()
    assert cat(spider, "Aurejärven kirkko")[0] == Categories.PLACE_OF_WORSHIP
    assert cat(spider, "Espoon Kirkkojärven skeittipaikka")[0] == Categories.LEISURE_PITCH
    assert cat(spider, "Kirkkokallion kuntoportaat")[0] == Categories.LEISURE_FITNESS_STATION


def test_discgolf_split_from_golf():
    spider = make_spider()
    assert cat(spider, "Rauma DiscGolfPark")[0] == Categories.LEISURE_DISC_GOLF_COURSE
    assert cat(spider, "Golfkenttä")[0] == Categories.LEISURE_GOLF_COURSE


def test_hospital_subunit_downgrade():
    spider = make_spider()
    assert cat(spider, "Satasairaala")[0] == Categories.HOSPITAL
    assert cat(spider, "Palliatiivinen yksikkö, Sastamalan sairaala")[0] == Categories.CLINIC
    assert cat(spider, "Päiväsairaala")[0] == Categories.CLINIC


def test_ticket_machine_with_payment():
    category, extra = cat(make_spider(), "Pysäköintilippuautomaatti 322, Töölöntori, korttimaksu")
    assert category == Categories.VENDING_MACHINE
    assert extra["vending"] == "parking_tickets"
    assert extra["payment:credit_cards"] == "yes"


def test_lastensuojelu_service_is_office():
    spider = make_spider()
    assert cat(spider, "Lastensuojelu")[0] == Categories.OFFICE_GOVERNMENT
    # Genitive residential compounds keep the facility filing.
    assert cat(spider, "Lastensuojelulaitos")[0] == Categories.SOCIAL_FACILITY


def test_group_home_subtypes():
    spider = make_spider()
    for fi in ("Ryhmäkoti Karkkula", "Outamon lastenkoti Noko"):
        category, extra = cat(spider, fi)
        assert category == Categories.SOCIAL_FACILITY, fi
        assert extra["social_facility"] == "group_home", fi
    assert cat(spider, "Palvelukoti Osmanrinne")[0] == Categories.NURSING_HOME


def test_church_denomination_scoped():
    category, extra = cat(make_spider(), "Pielaveden kirkko")
    assert category == Categories.PLACE_OF_WORSHIP
    assert extra == {"religion": "christian", "denomination": "lutheran"}


def test_youth_centre_without_enum():
    # Nuorisotila/talo resolve to extras-only youth tags, never generic.
    category, extra = cat(make_spider(), "Punkalaitumen Nuorisotila")
    assert category is None
    assert extra == {"amenity": "youth_centre"}


def test_medical_supply_shop():
    spider = make_spider()
    assert cat(spider, "CPAP-tarvikejakelu")[0] == Categories.SHOP_MEDICAL_SUPPLY
    assert cat(spider, "Hoitotarvikejakelu")[0] == Categories.SHOP_MEDICAL_SUPPLY


def test_keuda_college_not_office():
    assert cat(make_spider(), "Keuda Kerava")[0] == Categories.COLLEGE


def test_unmapped_stays_generic():
    # Opaque proper names with no evidence route to generic, never dropped.
    spider = make_spider()
    item = parsed(spider, channel("Tukipuu"))
    assert item.get_tag("amenity") == "yes"


def test_numberless_descriptive_road_stays_freeform():
    # Krakantien päässä shape: descriptive, kept freeform like service-map.
    item = addressed(make_spider(), "Krakantien päässä", "")
    assert item["street_address"] == "Krakantien päässä"


def test_rescue_assisted_living_from_description():
    # Naskali (channel d9355aeb): housing for the intellectually disabled.
    spider = make_spider()
    channel = {
        "serviceChannelDescriptions": [
            {"language": "fi", "value": "Naskali tarjoaa asumista ja siihen liittyviä palveluita kehitysvammaisille."}
        ]
    }
    assert spider._rescue_category(channel) == Categories.ASSISTED_LIVING


def test_rescue_plain_social_without_housing():
    spider = make_spider()
    channel = {"serviceChannelDescriptions": [{"language": "fi", "value": "Päivätoimintaa kehitysvammaisille."}]}
    assert spider._rescue_category(channel) == Categories.SOCIAL_FACILITY


def test_rescue_artwork_from_description():
    # Kala ja poika: Essi Renvallin veistos.
    spider = make_spider()
    channel = {"serviceChannelDescriptions": [{"language": "fi", "value": "Essi Renvallin Kala ja poika -veistos."}]}
    assert spider._rescue_category(channel) == Categories.TOURISM_ARTWORK


def test_rescue_ignores_unrelated_descriptions():
    spider = make_spider()
    assert (
        spider._rescue_category({"serviceChannelDescriptions": [{"language": "fi", "value": "Avoinna arkisin."}]})
        is None
    )
    assert spider._rescue_category({}) is None


# ---- Quadrant D: operator, contact, hours ----------------------------------


def test_register_keeper_carries_no_operator():
    from locations.items import Feature as _F

    spider = make_spider()
    item = _F()
    spider._apply_operator(item, "Suomen Apteekkariliitto")
    assert "operator" not in item
    assert spider.crawler.stats.get_value("ptv_fi/operator/register_keeper") == 1


def test_municipal_operator_with_wikidata():
    from locations.items import Feature as _F

    spider = make_spider()
    item = _F()
    spider._apply_operator(item, "Helsingin kaupunki")
    assert item["operator"] == "Helsingin kaupunki"
    assert item["operator_wikidata"] == "Q1757"


def test_branch_agency_kept_over_maintainer():
    from locations.items import Feature as _F

    spider = make_spider()
    item = _F()
    item["operator"] = "Kela"
    spider._apply_operator(item, "Kokemäen kaupunki")
    assert item["operator"] == "Kela"
    assert "operator_wikidata" not in item


def test_association_operator_flagged_private():
    from locations.items import Feature as _F

    spider = make_spider()
    item = _F()
    spider._apply_operator(item, "Olka ry")
    assert item["operator"] == "Olka ry"
    assert item["extras"]["operator:type"] == "private"


def test_generic_hotline_dropped():
    from locations.items import Feature as _F

    spider = make_spider()
    item = _F()
    spider._apply_contact(
        item,
        {
            "phoneNumbers": [{"prefixNumber": "+358 9", "number": "81621"}],
            "emails": [{"value": "info@esperi.fi"}],
            "webPages": [{"url": "https://example.fi/login"}],
        },
    )
    assert "phone" not in item
    assert "email" not in item
    assert "website" not in item


def test_per_location_contact_kept():
    from locations.items import Feature as _F

    spider = make_spider()
    item = _F()
    spider._apply_contact(
        item,
        {
            "phoneNumbers": [{"prefixNumber": "+358 50", "number": "9119693"}],
            "emails": [{"value": "mouhijarvi.kirjasto@sastamala.fi"}],
            "webPages": [{"url": "https://www.sastamala.fi/kirjasto"}],
        },
    )
    assert item["phone"] == "+358 50 9119693"
    assert item["email"] == "mouhijarvi.kirjasto@sastamala.fi"
    assert item["website"] == "https://www.sastamala.fi/kirjasto"


def _spans(open_from, open_to):
    return [
        {"dayFrom": d, "dayTo": "", "from": open_from, "to": open_to}
        for d in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
    ]


def test_hours_union_merge_overlapping_desks():
    # Nurse/counsellor/psychologist timetables union into visit hours;
    # phone-only sets are skipped.
    spider = make_spider()
    oh = spider._hours(
        {
            "serviceHours": [
                {
                    "serviceHourType": "DaysOfTheWeek",
                    "additionalInformation": [{"value": "Terveydenhoitaja"}],
                    "openingHour": _spans("08:00:00", "16:00:00"),
                },
                {
                    "serviceHourType": "DaysOfTheWeek",
                    "additionalInformation": [{"value": "Kuraattori"}],
                    "openingHour": _spans("08:00:00", "15:30:00"),
                },
                {
                    "serviceHourType": "DaysOfTheWeek",
                    "additionalInformation": [{"value": "Puhelinaika"}],
                    "openingHour": _spans("08:00:00", "10:00:00"),
                },
            ]
        },
        None,
    )
    assert oh.as_opening_hours() == "Mo-Fr 08:00-16:00"


def test_hours_dated_and_closed_shapes():
    spider = make_spider()
    assert (
        spider._hours(
            {
                "serviceHours": [
                    {
                        "serviceHourType": "DaysOfTheWeek",
                        "validFrom": "2027-01-01T00:00:00",
                        "openingHour": [{"dayFrom": "Monday", "dayTo": "", "from": "08:00:00", "to": "16:00:00"}],
                    },
                ]
            },
            None,
        )
        is None
    )
    assert (
        spider._hours(
            {
                "serviceHours": [
                    {
                        "serviceHourType": "DaysOfTheWeek",
                        "isClosed": True,
                        "openingHour": [{"dayFrom": "Monday", "dayTo": "", "from": "", "to": ""}],
                    },
                ]
            },
            None,
        )
        is None
    )


def test_kela_branch_end_to_end():
    # Kokemäen Asiointipiste/Kela, maintained by the city.
    spider = make_spider()
    item = parsed(spider, channel("Kokemäen Asiointipiste/Kela"), "Kokemäen kaupunki")
    assert item["name"] == "Kokemäen Asiointipiste"
    assert item["operator"] == "Kela"
    assert item["extras"]["official_name"] == "Kokemäen Asiointipiste/Kela"
    assert item["city"] == "Helsinki"


def test_imaging_branch_end_to_end():
    # Kuvantaminen, Pirkkala: the branch merely repeats the city, so no
    # branch (reviewer catch); the unit remainder still branches.
    spider = make_spider()
    item = parsed(spider, channel("Kuvantaminen, Pirkkala", office="PIRKKALA"), "Pirkanmaan hyvinvointialue")
    assert item["name"] == "Kuvantaminen"
    assert item.get("branch") is None
    assert item["city"] == "Pirkkala"
    item = parsed(
        spider, channel("Kuvantaminen, Pirkkala Pirkkalan röntgen", office="PIRKKALA"), "Pirkanmaan hyvinvointialue"
    )
    assert item["branch"] == "Pirkkalan röntgen"


def test_youth_exports_without_generic():
    spider = make_spider()
    item = parsed(spider, channel("Punkalaitumen Nuorisotila"), "Punkalaitumen kunta")
    assert item["extras"]["amenity"] == "youth_centre"
    assert item.get("amenity") is None


def test_square_exports_place_without_amenity():
    spider = make_spider()
    item = parsed(spider, channel("Töölöntori"), "Helsingin kaupunki")
    assert item["extras"]["place"] == "square"
    assert item.get("amenity") is None


def test_genitive_service_end_to_end():
    spider = make_spider()
    item = parsed(
        spider,
        channel("Rovastinkankaan koulun opiskeluhuolto, Orivesi", office="ORIVESI"),
        "Pirkanmaan hyvinvointialue",
    )
    assert item["name"] == "Opiskeluhuolto"
    assert item["located_in"] == "Rovastinkankaan koulu"
    assert item["extras"]["official_name"] == "Rovastinkankaan koulun opiskeluhuolto, Orivesi"


# ---- Address/city batch ----------------------------------------------------
# Municipality outranks the postal town; post office is fallback only.


def test_city_prefers_street_municipality():
    spider = make_spider()
    street = {"municipality": {"name": [{"language": "fi", "value": "Seinäjoki"}]}}
    assert spider._city_src(street, {"areas": []}, "KYLÄNPÄÄ") == "Seinäjoki"


def test_city_uses_single_area_municipality():
    spider = make_spider()
    channel = {"areas": [{"municipalities": [{"name": [{"language": "fi", "value": "Kuusamo"}]}]}]}
    assert spider._city_src({}, channel, "KUUSAMO") == "Kuusamo"


def test_city_multi_area_falls_back_to_post_office():
    spider = make_spider()
    channel = {
        "areas": [
            {
                "municipalities": [
                    {"name": [{"language": "fi", "value": "Helsinki"}]},
                    {"name": [{"language": "fi", "value": "Espoo"}]},
                ]
            }
        ]
    }
    assert spider._city_src({}, channel, "HELSINKI") == "HELSINKI"


def test_city_station_post_office_strips():
    assert make_spider()._city_src({}, {"areas": []}, "ORIVESI AS") == "ORIVESI"


def test_municipality_end_to_end():
    # Postal village Kylänpää must not leak into addr:city or name splits.
    spider = make_spider()
    data = channel("Neuvonta", road="Kylänpääntie", street_number="200", postcode="60420", office="KYLÄNPÄÄ")
    street = data["addresses"][0]["streetAddress"]
    street["municipality"] = {"name": [{"language": "fi", "value": "Seinäjoki"}]}
    item = parsed(spider, data, "Seinäjoen kaupunki")
    assert item["city"] == "Seinäjoki"


def test_coords_notreceived_and_failed_drop():
    spider = make_spider()
    base = {"latitude": "6672010", "longitude": "385128"}
    assert spider._coords({**base, "coordinateState": "NotReceived"}) is None
    assert spider._coords({**base, "coordinateState": "Failed"}) is None
    assert spider._coords({**base, "coordinateState": "Ok"}) is not None


def test_postcode_tail_stripped_from_number():
    # Voimapolku 3 03100 Nummela shape.
    item = addressed(make_spider(), "Voimapolku", "3 03100 Nummela", postcode="03100", office="NUMMELA")
    assert (item["street"], item["housenumber"]) == ("Voimapolku", "3")


def test_road_venue_prefix_split():
    spider = make_spider()
    assert spider._road_base("Didrichsenin taidemuseo, Kuusilahdenkuja") == "Kuusilahdenkuja"
    assert spider._road_base("Castreninkatu, puisto") == "Castreninkatu"
    assert spider._road_base("Rekipellonpuisto, Vesala") == "Rekipellonpuisto"


def test_road_venue_prefix_end_to_end():
    item = addressed(make_spider(), "Didrichsenin taidemuseo, Kuusilahdenkuja", "1")
    assert (item["street"], item["housenumber"]) == ("Kuusilahdenkuja", "1")


def test_island_zone_routes_to_place():
    # Talholmen virkistysalue: island site, zone-noun tail.
    item = addressed(make_spider(), "Talholmen virkistysalue", "")
    assert item["extras"]["addr:place"] == "Talholmen virkistysalue"
    assert "street_address" not in item


def test_island_street_suffix_stays_street():
    # Saaristonkatu contains saari but reads as a street.
    item = addressed(make_spider(), "Saaristonkatu", "")
    assert item["street"] == "Saaristonkatu"
    assert "street_address" not in item


def test_trailing_comma_boilerplate_end_to_end():
    # Live crasher (c052becb): trailing comma dodged the boilerplate strip,
    # then _split_comma fell off the end returning None and killed its
    # whole 40-batch. Name keeps the campaign title, signed form survives.
    spider = make_spider()
    item = parsed(
        spider,
        channel("Hae mukaan Hyvän olon polku -ryhmään! -palvelun järjestämispaikka,"),
        "Jyväskylän kaupunki",
    )
    assert item["name"] == "Hae mukaan Hyvän olon polku -ryhmään!"
    assert item["extras"]["official_name"] == "Hae mukaan Hyvän olon polku -ryhmään! -palvelun järjestämispaikka,"


def test_dangling_comma_names_head():
    # SYNTHETIC "Neuvonta," shape: empty tail, head names it.
    name, located, official = split(make_spider(), "Neuvonta,")
    assert name == "Neuvonta"
    assert located is None
    assert official == "Neuvonta,"


def test_split_name_never_returns_none():
    # Totality: adversarial punctuation must never crash the unpack in
    # _apply_naming (cf. the trailing-comma batch killer above).
    spider = make_spider()
    for probe in ("Neuvonta,", ",", " , ", "Kotihoito, ", "/", " / ", "A / B /", ",,,", "Nimi (", "Nimi ()"):
        result = spider._split_name(spider._clean_name(probe), None)
        assert result is not None and len(result) == 3, probe


# ---- Review round 6: categories ------------------------------------------------
# Ten subagents reviewed 1,000 fresh-crawl rows; everyadopt below was
# verified against the spider before implementation. Declined findings
# (Kiiminki tails, invented station names, official_name purism beyond
# the always-name:sv rule, city-homepage websites, switchboard phones,
# feed-error rows) are documented in the review triage, not here.


def test_tekonurmi_outranks_nurmikentta():
    # Leppävaaran urheilupuiston tekonurmikenttä 2: artificial, not grass.
    category, extra = cat(make_spider(), "Leppävaaran urheilupuiston tekonurmikenttä 2")
    assert category == Categories.LEISURE_PITCH
    assert extra == {"sport": "soccer", "surface": "artificial_turf"}


def test_beach_without_resort_and_plural():
    # Finnish swimming spots are not resorts (reviewer: resort invented).
    spider = make_spider()
    assert cat(spider, "Jänissaaren uimapaikka") == (Categories.NATURAL_BEACH, None)
    assert cat(spider, "Uimarannat")[0] == Categories.NATURAL_BEACH


def test_info_guards_and_matches():
    spider = make_spider()
    # Ryhmäkoti Sinfonia is a group home (ryhmäkoti wins); the info guard
    # only stops the tourism filing Sinfonia alone would trigger.
    category, extra = cat(spider, "Ryhmäkoti Sinfonia")
    assert category == Categories.SOCIAL_FACILITY
    assert extra == {"social_facility": "group_home"}
    assert cat(spider, "Sinfonia")[0] is None
    assert cat(spider, "Infopiste")[0] == Categories.TOURISM_INFORMATION
    assert cat(spider, "Pääinfo")[0] == Categories.TOURISM_INFORMATION


def test_tori_service_and_parking_guards():
    spider = make_spider()
    assert cat(spider, "Maahanmuuttajien ohjaus- ja palvelupiste Navigaattori")[1] != {"place": "square"}
    assert cat(spider, "Omnian Palvelutori")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Esteetön pysäköintialue Kivenlahdentori")[0] == Categories.PARKING


def test_koulu_compound_guards():
    spider = make_spider()
    assert cat(spider, "Koulutuskeskus Salpaus")[0] == Categories.COLLEGE
    assert cat(spider, "Aikuiskoulutus")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Koulutalo")[0] == Categories.SCHOOL
    assert cat(spider, "Soveltava temppuilu kouluikäisille")[0] is None  # school-aged, not a school


def test_seurakuntatalo_is_community():
    assert cat(make_spider(), "Keiteleen seurakuntatalo")[0] == Categories.COMMUNITY_CENTRE


def test_group_words_never_file_as_venue():
    spider = make_spider()
    assert cat(spider, "Anniksen enkelit -teatteriryhmä")[0] is None
    assert cat(spider, "Miesten kirjastoparlamentti")[0] is None
    # Peer-support groups are community venues, not generic activities.
    assert cat(spider, "Omaisten vertaistukiryhmä")[0] == Categories.COMMUNITY_CENTRE
    # Real venues sharing the words keep their filing.
    assert cat(spider, "Ryhmäkoti Karkkula")[0] == Categories.SOCIAL_FACILITY
    assert cat(spider, "Kerhotalo")[0] == Categories.COMMUNITY_CENTRE


def test_nurse_guard_outranks_daycare_host():
    spider = make_spider()
    for fi in (
        "Esiopetuksen opiskeluhuolto, Laurentius-päiväkoti",
        "Esiopetuksen opiskeluhuolto, Kantvikin päiväkoti",
        "Opiskeluhuolto, Karis svenska högstadium",
    ):
        category, extra = cat(spider, fi)
        assert category == Categories.CLINIC, fi
        assert extra == {"healthcare": "nurse"}, fi


def test_pool_track_vet_rows():
    spider = make_spider()
    assert cat(spider, "Uintikeskus")[0] == Categories.LEISURE_SPORTS_CENTRE
    assert cat(spider, "Pump track-rata")[0] == Categories.LEISURE_TRACK
    assert cat(spider, "Eläinlääkäri Eura")[0] == Categories.VETERINARY
    assert cat(spider, "Kampuksen kamppailutila")[0] == Categories.LEISURE_SPORTS_HALL
    assert cat(spider, "Stadin yhteisötalo Alppila")[0] == Categories.COMMUNITY_CENTRE
    assert cat(spider, "Käräjäsali")[0] == Categories.COURTHOUSE
    assert cat(spider, "Oulun käräjäoikeus, Ruskonselän istuntosali")[0] == Categories.COURTHOUSE
    assert cat(spider, "Kokkomäen puutarhajätealue")[0] == Categories.RECYCLING
    assert cat(spider, "Puokkarin nuokkari")[1] == {"amenity": "youth_centre"}


def test_kota_compound_final():
    spider = make_spider()
    assert cat(spider, "Vareskota")[0] == Categories.SHELTER
    assert cat(spider, "Ravintola Dakota")[0] == Categories.RESTAURANT


def test_ward_and_reception_rows():
    spider = make_spider()
    assert cat(spider, "Malmin osasto 13")[0] == Categories.CLINIC
    assert cat(spider, "Laakson osasto 3")[0] == Categories.CLINIC
    assert cat(spider, "Suursuon osasto 23")[0] == Categories.CLINIC
    assert cat(spider, "Kaupunginosan toimisto")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Vainajansäilytys, Ahveniston sairaala")[0] == Categories.CLINIC
    assert cat(spider, "Terveysaseman vastaanotto")[0] == Categories.CLINIC
    assert cat(spider, "Akaan lääkärin ja hoitajan vastaanotot")[0] == Categories.CLINIC
    assert cat(spider, "Kuntoutuksen poliklinikat")[0] == Categories.CLINIC
    assert cat(spider, "Mielialahäiriötyöryhmä, Tyks, Raisio")[0] == Categories.CLINIC
    assert cat(spider, "Diabeteskeskus")[0] == Categories.CLINIC
    assert cat(spider, "Maahanmuuttajien terveyspalvelut")[0] == Categories.CLINIC
    assert cat(spider, "Kuopion Canthia, suun perusterveydenhuolto")[0] == Categories.DENTIST


def test_therapy_rows_carry_clinic():
    spider = make_spider()
    assert cat(spider, "Fysioterapia Kankaanpää") == (
        Categories.CLINIC,
        {"healthcare": "physiotherapist"},
    )
    assert cat(spider, "Oriveden puheterapian vastaanotot") == (
        Categories.CLINIC,
        {"healthcare": "speech_therapist"},
    )


def test_care_home_rows():
    spider = make_spider()
    assert cat(spider, "Palvelut ikäihmisille")[0] == Categories.NURSING_HOME
    assert cat(spider, "Töölön seniorikeskus/Helmi ryhmäkoti")[0] == Categories.SOCIAL_FACILITY
    assert cat(spider, "Töölön seniorikeskus/Helmi ryhmäkoti")[1] == {"social_facility": "group_home"}


def test_court_keeps_sport():
    # Pallokenttä shadowed koripallo until the reorder.
    category, extra = cat(make_spider(), "Lounatuulenpuiston koripallokenttä")
    assert category == Categories.LEISURE_PITCH
    assert extra["sport"] == "basketball"
    assert cat(make_spider(), "Haminamäen Valio Areenan nurmikenttä")[0] == Categories.LEISURE_PITCH


def test_halli_end_anchored():
    spider = make_spider()
    assert cat(spider, "Säkylähalli")[0] == Categories.LEISURE_SPORTS_HALL
    assert cat(spider, "Talviharjoitteluhalli")[0] == Categories.LEISURE_SPORTS_HALL
    assert cat(spider, "Hallitus")[0] is None


def test_apuvaline_and_paja_filings():
    spider = make_spider()
    assert cat(spider, "Apuvälinepalvelu")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Miehikkälän työpaja")[1] == {"social_facility": "workshop"}


def test_inessive_host_category():
    # Services AT a venue never inherit it.
    assert cat(make_spider(), "Martat neuvoo Kuusankosken kirjastossa")[0] is None


# ---- Review round 6: names ----------------------------------------------------


def test_police_desk_qualifiers_stay_whole():
    spider = make_spider()
    for fi in (
        "Nurmeksen poliisiasema, löytötavarat",
        "Kuhmon poliisiasema, asetarkastus",
        "Pietarsaaren poliisiasema, aseen esitys",
        "Loimaan poliisiasema, poliisipäivystys",
    ):
        assert split(spider, fi) == (fi, None, None), fi
    # Permit desks split instead (service names, station locates).


def test_service_host_without_school_words():
    # Norlandia Linna hosts, like Karamzinin and Solglimtens before it.
    name, located, official = split(make_spider(), "Esiopetuksen opiskeluhuolto, Norlandia Linna")
    assert name == "Esiopetuksen opiskeluhuolto"
    assert located == "Norlandia Linna"
    assert official == "Esiopetuksen opiskeluhuolto, Norlandia Linna"


def test_swedish_service_tail():
    name, located, _ = split(make_spider(), "Zacharias Topeliusskolan, Smågruppsundervisning")
    assert name == "Smågruppsundervisning"
    assert located == "Zacharias Topeliusskolan"


def test_hogstadium_school_tail():
    name, located, _ = split(make_spider(), "Opiskeluhuolto, Karis svenska högstadium")
    assert name == "Opiskeluhuolto"
    assert located == "Karis svenska högstadium"


def test_qualifier_parens_stay_whole():
    spider = make_spider()
    assert split(spider, "Kuntoilulaitteet (ulko)") == ("Kuntoilulaitteet (ulko)", None, None)
    assert split(spider, "Kottby grundskola, Arabia kvartersskola, åk 1–2") == (
        "Kottby grundskola, Arabia kvartersskola, åk 1–2",
        None,
        None,
    )


def test_coverage_hyphen_fragment_kept():
    # Hyphen-fragment lists are one name, not municipality coverage.
    name, located, official = split(make_spider(), "Sovellettua jooga-, pilates- ja faskiaharjoittelua Tesoma")
    assert (name, located) == ("Sovellettua jooga-, pilates- ja faskiaharjoittelua Tesoma", None)
    assert official is None


def test_dash_facility_kept_whole():
    spider = make_spider()
    assert split(spider, "Virkeät Ikämiehet -toiminnan starttikurssi Sastamala")[0] == (
        "Virkeät Ikämiehet -toiminnan starttikurssi Sastamala"
    )
    assert split(spider, "Kuivalahden koulun 5 -väyläinen frisbeegolfrata")[0] == (
        "Kuivalahden koulun 5 -väyläinen frisbeegolfrata"
    )
    assert split(spider, "Ulkokuntoilusalit ja -alueet")[0] == "Ulkokuntoilusalit ja -alueet"


def test_colon_city_and_operator():
    spider = make_spider()
    assert split(spider, "Outokumpu: Vertaisryhmä", "Outokumpu") == ("Vertaisryhmä", None, "Outokumpu: Vertaisryhmä")
    assert split(spider, "OLKA-pisteen teemapäivä: Saimaan Syöpäyhdistys ry") == (
        "OLKA-pisteen teemapäivä",
        None,
        "OLKA-pisteen teemapäivä: Saimaan Syöpäyhdistys ry",
    )


def test_space_city_tail():
    spider = make_spider()
    assert split(spider, "Kuntoutusohjaus Kankaanpää", "Kankaanpää") == (
        "Kuntoutusohjaus",
        None,
        "Kuntoutusohjaus Kankaanpää",
    )
    assert split(spider, "Toimintakeskus Parikkala", "Parikkala")[0] == "Toimintakeskus"


def test_no_branch_on_schools():
    spider = make_spider()
    item = parsed(
        spider, channel("Tampereen seudun työväenopiston toimisto: Sampola", office="TAMPERE"), "Tampereen kaupunki"
    )
    assert item["name"] == "Tampereen seudun työväenopiston toimisto: Sampola"
    assert item.get("branch") is None


def test_inessive_host_split():
    name, located, official = split(make_spider(), "Martat neuvoo Kuusankosken kirjastossa")
    assert name == "Martat neuvoo"
    assert located == "Kuusankosken kirjasto"
    assert official == "Martat neuvoo Kuusankosken kirjastossa"


def test_bare_slash_service_and_genitive():
    spider = make_spider()
    assert split(spider, "Töölön seniorikeskus/Helmi ryhmäkoti") == (
        "Helmi ryhmäkoti",
        "Töölön seniorikeskus",
        "Töölön seniorikeskus/Helmi ryhmäkoti",
    )
    assert split(spider, "Keuruun yläkoulun/lukion tanssisali") == (
        "Keuruun yläkoulun/lukion tanssisali",
        None,
        None,
    )


def test_located_is_city_dropped():
    spider = make_spider()
    item = parsed(spider, channel("Jumppa / Lahti", road="Katu", street_number="1", office="LAHTI"), "Lahden kaupunki")
    assert item.get("located_in") is None
    assert item["city"] == "Lahti"


def test_name_and_located_capitalized():
    spider = make_spider()
    item = parsed(spider, channel("vaatelahjoitus"), "Verso ry")
    assert item["name"] == "Vaatelahjoitus"
    item = parsed(
        spider,
        channel("Kokemäen äitiysneuvola, perhekeskus Suvituuli", office="KOKEMÄKI"),
        "Satakunnan hyvinvointialue",
    )
    assert item["located_in"] == "Perhekeskus Suvituuli"


# ---- Review round 6: addresses ------------------------------------------------


def test_kurvi_street_suffix():
    item = addressed(make_spider(), "Sankarinkurvi", "")
    assert item["street"] == "Sankarinkurvi"
    assert "street_address" not in item


def test_road_case_fixed():
    item = addressed(make_spider(), "wetterhoffinkatu", "2")
    assert (item["street"], item["housenumber"]) == ("Wetterhoffinkatu", "2")


def test_postcode_in_unit_dropped():
    spider = make_spider()
    assert spider._number_tail("03100 Nummela") is None


def test_dup_number_folded():
    item = addressed(make_spider(), "Painiityntie", "21 ja 21")
    assert (item["street"], item["housenumber"]) == ("Painiityntie", "21")


def test_premise_unit_split():
    item = addressed(make_spider(), "Leonkatu", "4 Liiketila 3B-120")
    assert (item["street"], item["housenumber"]) == ("Leonkatu", "4")
    assert "street_address" not in item
    assert item["extras"]["addr:unit"] == "Liiketila 3B-120"


def test_bare_letter_unit_rules():
    spider = make_spider()
    item = addressed(spider, "Katu", "1, B")
    assert (item["street"], item["housenumber"]) == ("Katu", "1")
    assert item["extras"]["addr:unit"] == "B"
    # Folded duplication ("2B, B" feeds both paths): the unit drops.
    item = addressed(spider, "Laivalahdenkatu", "2B, B")
    assert (item["street"], item["housenumber"]) == ("Laivalahdenkatu", "2b")
    assert "street_address" not in item
    assert "addr:unit" not in item["extras"]


def test_swedish_floor_parsed():
    spider = make_spider()
    assert spider._number_tail("2 vån") is None
    item = addressed(spider, "Katu", "1, 2 vån")
    assert (item["street"], item["housenumber"]) == ("Katu", "1")
    assert item["extras"]["addr:floor"] == "2"


def test_paren_floor_parsed():
    # 7 A (3. kerros), including the word-form 7 A (kolmannes kerros).
    for number, expected in (("7 A (3. kerros)", "3"), ("7 A (kolmannes kerros)", "3")):
        item = addressed(make_spider(), "Tie", number)
        assert (item["street"], item["housenumber"]) == ("Tie", "7"), number
        assert item["extras"]["addr:unit"] == "A", number
        assert item["extras"]["addr:floor"] == expected, number
        assert "level" not in item["extras"]


def test_word_ordinal_floor_parsed():
    # 4 a, toinen. krs shape (live feed row).
    item = addressed(make_spider(), "Katu", "4 a, toinen. krs")
    assert item["extras"]["addr:floor"] == "2"
    assert "level" not in item["extras"]


def test_multi_floor_list_dropped():
    # 5, 3. ja 4. krs: ambiguous across floors, no addr:floor.
    item = addressed(make_spider(), "Tie", "5, 3. ja 4. krs")
    assert (item["street"], item["housenumber"]) == ("Tie", "5")
    assert "addr:floor" not in item["extras"]


def test_ordinal_street_name_not_floor():
    # Toinen linja is a street, never a floor: markers are required.
    item = addressed(make_spider(), "Toinen linja", "")
    assert "addr:floor" not in item["extras"]


def test_ordinal_street_with_real_floor():
    # Viides linja 9, 2. krs: the street ordinal is not a floor, the
    # marker-anchored 2 is.
    item = addressed(make_spider(), "Viides linja", "9, 2. krs")
    assert (item["street"], item["housenumber"]) == ("Viides linja", "9")
    assert item["extras"]["addr:floor"] == "2"


def test_street_level_note_dropped():
    # 13, katutaso: ambiguous numbering, stays dropped, never level.
    item = addressed(make_spider(), "Katu", "13, katutaso")
    assert (item["street"], item["housenumber"]) == ("Katu", "13")
    assert "addr:floor" not in item["extras"]
    assert "level" not in item["extras"]


def test_centralized_service_kept_whole():
    # Opiskeluterveydenhuolto, keskitetty palvelu Espoo ja Kauniainen:
    # coverage descriptors are not venues; the signed form stays whole.
    signed = "Opiskeluterveydenhuolto, keskitetty palvelu Espoo ja Kauniainen"
    assert split(make_spider(), signed) == (signed, None, None)


def test_source_links_suomi_fi_service_point():
    # Every channel carries its stable Suomi.fi service-point page.
    item = parsed(make_spider(), channel("Vojakkalan uimapaikka, Kaartjärvi"))
    assert item["extras"]["source"] == (
        "https://www.suomi.fi/palvelut/palvelupiste/11111111-1111-4111-8111-111111111111"
    )


def test_check_date_from_modified():
    # The Suomi.fi "Päivitetty" date rides along as check_date.
    ch = channel("Vojakkalan uimapaikka, Kaartjärvi")
    ch["modified"] = "2026-10-08T08:00:00.000000"
    assert parsed(make_spider(), ch)["extras"]["check_date"] == "2026-10-08"


# ---- Review round 8: categories ----------------------------------------------


def test_rescue_station_rows():
    spider = make_spider()
    assert cat(spider, "Mellunkylän pelastusasema")[0] == Categories.FIRE_STATION
    assert cat(spider, "Kiviniemen VPK")[0] == Categories.FIRE_STATION
    assert cat(spider, "Savitaipaleen liikuntatalo")[0] == Categories.LEISURE_SPORTS_CENTRE


def test_sport_facility_outranks_hall():
    spider = make_spider()
    category, extra = cat(spider, "Katajanokan liikuntahalli / Yhden korin koripallokenttä")
    assert category == Categories.LEISURE_PITCH
    assert extra["sport"] == "basketball"
    assert cat(spider, "Koripallohalli")[1]["sport"] == "basketball"


def test_waste_and_desk_rows():
    spider = make_spider()
    assert cat(spider, "Korvenmäen jätekeskus")[0] == Categories.RECYCLING
    assert cat(spider, "Kempeleen vaarallisen jätteen vastaanotto")[0] == Categories.RECYCLING
    assert cat(spider, "Mänttä-Vilppulan lapsiperheiden sosiaalipalvelujen vastaanotot")[0] == (
        Categories.OFFICE_GOVERNMENT
    )
    assert cat(spider, "Pirkanmaan oikeusaputoimisto")[0] == Categories.OFFICE_LAWYER
    assert cat(spider, "Haapajärven päihdepalvelujen toimipiste")[0] == Categories.CLINIC
    assert cat(spider, "Museoiden toimisto")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Teerijärven hyvinvointiasema, fysioterapia")[1] == {"healthcare": "physiotherapist"}


def test_host_facility_reorders():
    spider = make_spider()
    assert cat(spider, "Korkeasaaren eläintarhan lipunmyynti")[1] == {"shop": "tickets"}
    assert cat(spider, "Topeliuksen puiston yleisövessa")[0] == Categories.TOILETS
    assert cat(spider, "Maaseutupalvelut, Rovaniemen toimipiste")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Eläintarhan huvila")[0] is None
    assert cat(spider, "Linnavuoren palvelukodit")[0] == Categories.NURSING_HOME
    assert cat(spider, "Perhepäivähoitaja Tiia Ruotsalainen")[0] == Categories.KINDERGARTEN
    assert cat(spider, "Agricolanpuistikon koirakäymälä")[1] == {"amenity": "dog_toilet"}
    assert cat(spider, "Kämärin jääurheilukeskus")[0] == Categories.LEISURE_SPORTS_CENTRE
    assert cat(spider, "Kädentaitopaja")[1] == {"social_facility": "workshop"}
    assert cat(spider, "Jokiuomanpuiston kuntoilupaikka")[0] == Categories.LEISURE_FITNESS_STATION
    assert cat(spider, "Kliininen neurofysiologia, Porvoon sairaala")[0] == Categories.CLINIC
    assert cat(spider, "Karhuvuoren seurakuntakoti")[0] == Categories.COMMUNITY_CENTRE
    assert cat(spider, "Lahjanpuiston kerhohuone")[0] == Categories.COMMUNITY_CENTRE
    assert cat(spider, "Kouluravintola, Pukinmäenkaaren peruskoulu")[0] == Categories.CANTEEN


def test_sport_and_clinic_specials():
    spider = make_spider()
    assert cat(spider, "Saarikenttä- pesäpallostadion")[1] == {"sport": "pesapallo"}
    assert cat(spider, "Pisanpuiston petanque-kenttä")[1] == {"sport": "petanque"}
    assert cat(spider, "Rikosuhripäivystyksen Keski-Pohjanmaan palvelupiste")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Yläjärven talousneuvola")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Hyrynsalmen muistineuvola") == (Categories.CLINIC, None)
    assert cat(spider, "Lentotulli")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Kiskon äitiys- ja lastenneuvola")[1] == {"healthcare:speciality": "maternal_and_child_health"}


def test_shore_facility_bail():
    spider = make_spider()
    assert cat(spider, "Lauttasaaren uimaranta / Beachvolleykenttä")[1] == {"sport": "beachvolleyball"}
    assert cat(spider, "Päiväkoti Ankkalampi Duckies, Herttoniemenranta")[0] == Categories.KINDERGARTEN
    assert cat(spider, "Kotihoito Lappeenranta Läntinen")[0] == Categories.SOCIAL_FACILITY
    assert cat(spider, "Saunalahden venesatama")[0] == Categories.MARINA
    assert cat(spider, "Munkkiniemen uimaranta / Huoltorakennus")[0] is None


def test_phone_normalization():
    spider = make_spider()
    assert spider._normalize_phone("094711") == "+358 9 4711"
    assert spider._normalize_phone("0206156605") == "+358 206156605"
    assert spider._normalize_phone("+358 0503273734") == "+358 50 3273734"
    assert spider._normalize_phone("+358 358447851490") == "+358 44 7851490"
    assert spider._normalize_phone("+358 49460076255") is None
    assert spider._normalize_phone("116006") == "116006"


def test_partnership_and_acronym_operators():
    spider = make_spider()
    assert spider._is_private_org("Teatterikoulu ILMI Ö.") is True
    assert spider._is_private_org("Rikosuhripäivystys - RIKU") is True
    assert spider._is_private_org("Eerikinkatu 1") is False


# ---- Review round 8: names ----------------------------------------------------


def test_slash_street_head_drops():
    spider = make_spider()
    name, located, official = split(spider, "Kurkisuontie 2 / Hiekkakenttä")
    assert name == "Hiekkakenttä"
    assert located is None
    assert official == "Kurkisuontie 2 / Hiekkakenttä"
    assert split(spider, "Kenttäpolku/Kouluravintola")[0] == "Kouluravintola"


def test_slash_numbered_building_qualifies():
    name, located, official = split(make_spider(), "Eläintarhan urheilukenttä / Huoltorakennus 4")
    assert name == "Eläintarhan urheilukenttä"
    assert located is None
    assert official == "Eläintarhan urheilukenttä / Huoltorakennus 4"


def test_slash_self_named_kept():
    signed = "Linnunlauluntien ulkokuntosali / Ulkokuntosali"
    assert split(make_spider(), signed) == (signed, None, None)


def test_slash_venue_needs_evidence():
    assert split(make_spider(), "Aamulla / Vasikat") == ("Aamulla / Vasikat", None, None)


def test_slash_service_proper_names_service():
    name, located, official = split(make_spider(), "Iltapäivätoiminta / Leikkipuisto Nurkka")
    assert name == "Iltapäivätoiminta"
    assert located == "Leikkipuisto Nurkka"
    assert official == "Iltapäivätoiminta / Leikkipuisto Nurkka"


def test_comma_room_names_facility():
    name, located, _ = split(make_spider(), "Vaajakummun koulu, luistelukenttä")
    assert name == "luistelukenttä"
    assert located == "Vaajakummun koulu"


def test_comma_street_tail_drops():
    name, located, official = split(make_spider(), "Kouluravintola, Pukinmäenkaaren peruskoulu, Kenttäpolku")
    assert name == "Kouluravintola, Pukinmäenkaaren peruskoulu"
    assert located is None
    assert official == "Kouluravintola, Pukinmäenkaaren peruskoulu, Kenttäpolku"


def test_paren_village_kept_with_city():
    name, located, official = split(make_spider(), "Juhananpuiston leikkipaikka (Idänpää)", "Hämeenlinna")
    assert (name, located, official) == ("Juhananpuiston leikkipaikka (Idänpää)", None, None)


def test_paren_status_notes_strip():
    spider = make_spider()
    assert split(spider, "Päiväkoti Peukalopotti (lakkautettu)")[0] == "Päiväkoti Peukalopotti"
    assert split(spider, "Virkkalan päiväkoti (väistö)")[0] == "Virkkalan päiväkoti"
    assert split(spider, "Hanhikosken ryhmäperhepäivähoito (toiminta loppunut 31.7.2024)")[0] == (
        "Hanhikosken ryhmäperhepäivähoito"
    )


def test_mm_coverage_drops():
    name, located, official = split(make_spider(), "Lastensuojelun jälkihuolto, mm. Iisalmi, Keitele")
    assert name == "Lastensuojelun jälkihuolto"
    assert located is None
    assert official == "Lastensuojelun jälkihuolto, mm. Iisalmi, Keitele"


def test_dash_org_kept():
    signed = "Luoteis-Savon Maaseutupalvelut - Kiuruveden maataloustoimisto"
    assert split(make_spider(), signed) == (signed, None, None)


def test_city_dash_prefix_dropped():
    from locations.items import Feature as _F

    spider = make_spider()
    item = _F()
    spider._apply_naming(
        item,
        {"fi": "Jämsä – päivätoimintaa kuntoutujille"},
        "Jämsä – päivätoimintaa kuntoutujille",
        "Jämsä",
    )
    assert item["name"] == "Päivätoimintaa kuntoutujille"
    assert item["extras"]["official_name"] == "Jämsä – päivätoimintaa kuntoutujille"


def test_comma_facility_venue():
    name, located, official = split(make_spider(), "Kahluuallas, Leikkipuisto Traktori")
    assert name == "Kahluuallas"
    assert located == "Leikkipuisto Traktori"
    assert official == "Kahluuallas, Leikkipuisto Traktori"


def test_comma_area_unit_kept():
    spider = make_spider()
    assert split(spider, "Puheterapia, Tikkurilan alue", "Vantaa") == (
        "Puheterapia, Tikkurilan alue",
        None,
        None,
    )
    assert split(spider, "Fysioterapia, Himangan yksikkö", "Kalajoki") == (
        "Fysioterapia, Himangan yksikkö",
        None,
        None,
    )


def test_ajanvaraus_stem_strips():
    name, located, official = split(
        make_spider(), "Ylivieskan oikeusaputoimisto, Haapaveden toimipaikka (vain ajanvarauksella)"
    )
    assert name == "Ylivieskan oikeusaputoimisto, Haapaveden toimipaikka"
    assert located is None
    assert official == "Ylivieskan oikeusaputoimisto, Haapaveden toimipaikka (vain ajanvarauksella)"


# ---- Service/ontology rescue --------------------------------------------------


def test_rescue_service_types_opaque():
    # Maya (opaque proper name) via its linked service name.
    ch = channel("Maya")
    ch["services"] = [{"service": {"name": "Maya tukiasunto Pietarsaaressa"}}]
    item = parsed(make_spider(), ch)
    assert item["extras"]["social_facility"] == "assisted_living"


def test_rescue_ontology_types_opaque():
    # Admin-shaped services fall through to the YSO ontology terms.
    ch = channel("Maya")
    ch["services"] = [{"service": {"name": "Liikunnan ja urheilun tulosyksikkö"}}]
    ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": "päiväkotihoito"}]}]
    item = parsed(make_spider(), ch)
    assert item.get_tag("amenity") == "kindergarten"


def test_rescue_service_extras():
    # Placement-only rescue carries tags without a POI category.
    ch = channel("Maya")
    ch["services"] = [{"service": {"name": "Eläintarhan myymälä"}}]
    item = parsed(make_spider(), ch)
    assert item["extras"]["shop"] == "yes"


def test_rescue_art_from_any_language():
    # Eino Leino documents public art outside Finnish; rescue reads all.
    ch = channel("Eino Leino")
    ch["serviceChannelDescriptions"] = [
        {"language": "fi", "value": "Eino Leino julkista taidetta."},
        {"language": "en", "value": "Eino Leino is a work of public art."},
    ]
    assert parsed(make_spider(), ch).get_tag("tourism") == "artwork"


def test_rescue_skips_generic_admin_labels():
    # "Varhaiskasvatus" files as an office, so it must not shadow the
    # specific ontology behind it ("päiväkotihoito" → kindergarten).
    # Covers Lastentalo Kuusipiha and Satukontti (c4926d69).
    for name in ("Lastentalo Kuusipiha", "Satukontti"):
        ch = channel(name)
        ch["services"] = [{"service": {"name": "Varhaiskasvatus"}}]
        ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": "päiväkotihoito"}]}]
        assert parsed(make_spider(), ch).get_tag("amenity") == "kindergarten", name


def test_maaseutupalvelut_is_office():
    # Mid-compound tupa ("maaseuTUPAlvelut") must not file community.
    assert cat(make_spider(), "Maaseutupalvelut")[0] == Categories.OFFICE_GOVERNMENT


def test_comma_water_venue_split():
    # Lakes and waters name venues ("Vojakkalan uimapaikka, Kaartjärvi").
    name, located, official = split(make_spider(), "Vojakkalan uimapaikka, Kaartjärvi")
    assert name == "Vojakkalan uimapaikka"
    assert located == "Kaartjärvi"
    assert official == "Vojakkalan uimapaikka, Kaartjärvi"


def test_veneranta_is_marina():
    spider = make_spider()
    assert cat(spider, "Loppijärvi, Kuljun veneranta")[0] == Categories.MARINA
    assert cat(spider, "Halsuan keskustan uimaranta ja veneranta")[0] == Categories.MARINA
    assert cat(spider, "Veneranta, Leppävesi")[0] == Categories.MARINA
    # Named facilities at the shore still file as themselves.
    assert cat(spider, "Munkkiniemen uimaranta")[0] == Categories.NATURAL_BEACH


def test_camp_centre_is_camp_site():
    # Näätähiekan leirikeskus: camp centres are unambiguous.
    assert cat(make_spider(), "Näätähiekan leirikeskus")[0] == Categories.TOURISM_CAMP_SITE


def test_boat_launch_ramp_is_slipway():
    # Ipo-Kiusalan veneenlaskupaikka: boat launch ramps are unambiguous.
    assert cat(make_spider(), "Ipo-Kiusalan veneenlaskupaikka")[0] == Categories.LEISURE_SLIPWAY


def test_court_and_concert_rows():
    spider = make_spider()
    assert cat(spider, "Hovioikeus")[0] == Categories.COURTHOUSE
    assert cat(spider, "Konserttitalo")[0] == Categories.EVENTS_VENUE


def test_hobby_premises_are_community():
    # Maskutalo (4fac6e98) via its Harrastetilat service.
    assert cat(make_spider(), "Harrastetilat")[0] == Categories.COMMUNITY_CENTRE


def test_graffiti_wall_is_artwork():
    spider = make_spider()
    assert cat(spider, "Lausteen taidekontti")[0] == Categories.TOURISM_ARTWORK
    assert cat(spider, "Taidekontit ja graffitiseinä")[1] == {"artwork_type": "graffiti"}


def test_aid_distribution_is_social():
    assert cat(make_spider(), "Naulakko - vaate- ja tavara-apu")[0] == Categories.SOCIAL_FACILITY


def test_memory_clinic_is_clinic():
    # Muistikeskus (0ea339f6): memory clinics are health care.
    assert cat(make_spider(), "Raision Muistikeskus")[0] == Categories.CLINIC


def test_4h_clubs_are_community():
    spider = make_spider()
    assert cat(spider, "Itätuulen 4H-kerho")[0] == Categories.COMMUNITY_CENTRE
    assert cat(spider, "4H-kerho")[0] == Categories.COMMUNITY_CENTRE


def test_peer_support_groups_are_community():
    spider = make_spider()
    assert cat(spider, "Omaistaan hoitavien vertaisryhmät")[0] == Categories.COMMUNITY_CENTRE
    assert cat(spider, "Vertaistukiryhmä syöpään sairastuneille")[0] == Categories.COMMUNITY_CENTRE
    assert cat(spider, "Imatran Sydänkerho")[0] == Categories.COMMUNITY_CENTRE
    assert cat(spider, "Sydänosasto")[0] == Categories.CLINIC
    # Child-welfare framing keeps its existing filing.
    assert cat(spider, "Lastensuojelun ja perhesosiaalityön vertaisryhmätoiminta")[0] == (Categories.SOCIAL_FACILITY)


def test_senior_clubs_are_social():
    spider = make_spider()
    assert cat(spider, "Suomenkielinen seniorikerho")[0] == Categories.SOCIAL_FACILITY
    assert cat(spider, "Seniorikerho")[0] == Categories.SOCIAL_FACILITY


def test_found_animals_are_shelters():
    spider = make_spider()
    assert cat(spider, "Löytöeläimet Eura")[1] == {"amenity": "animal_shelter"}
    assert cat(spider, "Porin löytökissat")[1] == {"amenity": "animal_shelter"}


def test_patient_ombudsman_is_office():
    spider = make_spider()
    assert cat(spider, "Potilasasiavastaava")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Potilasasiamiehen asiointipaikka, Forssan sairaala")[0] == Categories.OFFICE_GOVERNMENT


def test_food_aid_is_social():
    spider = make_spider()
    assert cat(spider, "Ruoka-apua (leipää)")[0] == Categories.SOCIAL_FACILITY
    assert cat(spider, "Ruokajako")[0] == Categories.SOCIAL_FACILITY


def test_service_housing_is_nursing():
    # Ympärivuorokautinen palveluasuminen (8752969f): 24h service housing.
    spider = make_spider()
    assert cat(spider, "Ympärivuorokautinen palveluasuminen")[0] == Categories.NURSING_HOME
    assert cat(spider, "Koskelan palveluasumisyksikkö")[0] == Categories.NURSING_HOME


def test_housing_services_are_social():
    spider = make_spider()
    assert cat(spider, "Asumispalvelut kehitysvammaisille lapsille")[0] == Categories.SOCIAL_FACILITY
    assert cat(spider, "Kauklahden asumispalvelut")[0] == Categories.SOCIAL_FACILITY
    assert cat(spider, "Asumispalveluyksikkö Virrankoti")[1] == {"social_facility": "group_home"}


def test_event_venues_need_venue_nouns():
    spider = make_spider()
    assert cat(spider, "Tapahtumatalo")[0] == Categories.EVENTS_VENUE
    assert cat(spider, "Tapahtuma-alue")[0] == Categories.EVENTS_VENUE
    assert cat(spider, "Tapahtumalava")[0] == Categories.EVENTS_VENUE
    assert cat(spider, "Tapahtumayksikkö")[0] is None
    assert cat(spider, "Jäsentapahtumat ja luennot")[0] is None


def test_admin_units_are_offices():
    spider = make_spider()
    assert cat(spider, "Perusopetus")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Henkilöstöosasto")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Joroisten kunnan elinkeinotoimi")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Vihdin kunnan kulttuuri- ja vapaa-aika")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Maankäyttö- ja asumispalvelut")[0] == Categories.OFFICE_GOVERNMENT
    # Digiopastus is an activity, never a desk (26 rows at libraries).
    assert cat(spider, "Joen Severin digiopastus")[0] is None


def test_adessive_hosts_split_and_generic():
    spider = make_spider()
    name, located, official = named(
        spider, "Digiopastusta ikäihmisille Tesoman kirjastossa -palvelun järjestämispaikka"
    )
    assert name == "Digiopastusta ikäihmisille"
    assert located == "Tesoman kirjasto"
    assert cat(spider, "Joen Severin digiopastus Karsikon kirjastolla")[0] is None
    name, located, official = split(spider, "Vertaistukea Parkinsonia sairastavalle, K-U:lla")
    assert name == "Vertaistukea Parkinsonia sairastavalle"
    assert located is None


def test_association_houses_are_community():
    assert cat(make_spider(), "Pohjanmaan Yhdistykset ry")[0] == Categories.COMMUNITY_CENTRE


def test_ward_units_are_clinics():
    spider = make_spider()
    assert cat(spider, "Leikkaus ja anestesia")[0] == Categories.CLINIC
    assert cat(spider, "Leikkaushoitokeskus")[0] == Categories.CLINIC
    assert cat(spider, "Sisätaudit")[0] == Categories.CLINIC
    assert cat(spider, "Silmätautien hoito")[0] == Categories.CLINIC
    assert cat(spider, "Syöpätaudit ja sädehoito")[0] == Categories.CLINIC
    assert cat(spider, "Syöpätautien ja verisairauksien sairaansijat")[0] == Categories.CLINIC
    assert cat(spider, "Munuaisyksikkö")[0] == Categories.CLINIC
    assert cat(spider, "Tähystys")[0] == Categories.CLINIC
    assert cat(spider, "Dialyysi- ja munuaisyksikkö")[0] == Categories.CLINIC
    assert cat(spider, "Neulanvaihtopiste")[0] == Categories.CLINIC
    assert cat(spider, "Tartuntataudit")[0] == Categories.CLINIC


def test_daycare_plurals_rescue():
    # Kauklahden Ankkalampi-Duckies (2b14fde0): päiväkodit gradation.
    assert cat(make_spider(), "Espoon keskuksen yksityisen hoidon tuen päiväkodit")[0] == (Categories.KINDERGARTEN)


def test_harbour_berths_are_marinas():
    assert cat(make_spider(), "Tuomalan rannan venepaikat")[0] == Categories.MARINA


def test_emergency_housing_is_shelter():
    assert cat(make_spider(), "Hätämajoitusyksikkö Viisikko")[0] == Categories.SHELTER


def test_meeting_centres_are_social():
    # All 9 neuvottelukeskus rows are family-affairs desks.
    assert cat(make_spider(), "Perheasiain neuvottelukeskus")[0] == Categories.SOCIAL_FACILITY


def test_company_names_are_company_offices():
    spider = make_spider()
    assert cat(spider, "Imatran Seudun Kehitysyhtiö Oy")[0] == Categories.OFFICE_COMPANY
    assert cat(spider, "Ylämyllyn yritystalot")[0] == Categories.OFFICE_COMPANY
    assert cat(spider, "Kiinteistö Oy Keskiväli")[0] == Categories.OFFICE_COMPANY


def test_wellbeing_and_range_rows():
    spider = make_spider()
    assert cat(spider, "Terveys- ja hyvinvointikeskus")[0] == Categories.CLINIC
    assert cat(spider, "Ampumarata")[1] == {"leisure": "shooting_ground", "sport": "shooting"}
    assert cat(spider, "Ampumaradat")[1] == {"leisure": "shooting_ground", "sport": "shooting"}
    assert cat(spider, "Kurkvuoren moottoriurheilualue")[0] == Categories.LEISURE_PITCH
    assert cat(spider, "Kurkvuoren moottoriurheilualue")[1] == {"sport": "motor"}


def test_day_centres_and_brigades():
    spider = make_spider()
    assert cat(spider, "Lohjan päiväaikainen toiminta")[0] == Categories.SOCIAL_FACILITY
    assert cat(spider, "Hervannan vapaa-aikakeskus")[0] == Categories.COMMUNITY_CENTRE
    assert cat(spider, "Kakskerran Sopimuspalokunta")[0] == Categories.FIRE_STATION


def test_islands_are_islands():
    spider = make_spider()
    assert cat(spider, "Villaluodot Läntinen saari")[1] == {"place": "island"}
    assert cat(spider, "Saarentie 5")[0] is None
    assert cat(spider, "Koivuhaan arboretum")[1] == {"leisure": "botanical_garden"}


def test_audience_genitive_names_stay_whole():
    # Kuntosali yhdistyksen jäsenille (96a7762e): audience, not operator.
    spider = make_spider()
    assert spider._clean_name("Kuntosali yhdistyksen jäsenille -palvelun järjestämispaikka") == (
        "Kuntosali yhdistyksen jäsenille"
    )
    item = parsed(spider, channel("Kuntosali yhdistyksen jäsenille -palvelun järjestämispaikka"))
    assert item["name"] == "Kuntosali yhdistyksen jäsenille"
    assert cat(spider, "Kuntosali yhdistyksen jäsenille")[0] == Categories.GYM


def test_street_head_city_drops():
    # Pyhämäntie, Janakkala, Vammaisten asumispalvelut (b27207e0).
    name, located, official = split(make_spider(), "Pyhämäntie, Janakkala, Vammaisten asumispalvelut", "Janakkala")
    assert name == "Vammaisten asumispalvelut"
    assert located is None
    assert official == "Pyhämäntie, Janakkala, Vammaisten asumispalvelut"


def test_translation_suffix_is_not_bilingual():
    # Språkcafé season qualifier (4dcbc7d6): suffix strips, rest stays whole.
    signed = "Språkcafé på svenska i Ode bibliotek - Syksy 2026 -palvelun järjestämispaikka"
    item = parsed(make_spider(), channel(signed))
    assert item["name"] == "Språkcafé på svenska i Ode bibliotek - Syksy 2026"
    assert item["extras"]["official_name"] == signed


def test_copied_translations_skip():
    # Steinergymnasiet (8006efd6): sv/en copies of the signed form drop.
    signed = "Steinergymnasiet (Rudolf Steinerskolan i Helsingfors)"
    item = parsed(make_spider(), channel(signed, sv=signed, en=signed))
    assert item["name"] == "Steinergymnasiet"
    assert "name:sv" not in item["extras"]
    assert "name:en" not in item["extras"]


def test_survey_offices_split_by_municipality():
    spider = make_spider()
    assert split(spider, "Maanmittauslaitos Oulu", "Oulu") == (
        "Maanmittauslaitos",
        None,
        "Maanmittauslaitos Oulu",
    )
    # Ivalo is a village in Inari: the qualifier stays.
    assert split(spider, "Maanmittauslaitos Ivalo", "Inari") == ("Maanmittauslaitos Ivalo", None, None)


def test_trailing_pipe_strips():
    # Vertaistukiryhmä pipe record (cb9faf25) after the Kokkola strip.
    name, _, _ = split(make_spider(), "Vertaistukiryhmä | Uskontojen uhrien tuki Uut ry | Kokkola", "Kokkola")
    assert name == "Vertaistukiryhmä | Uskontojen uhrien tuki Uut ry"


def test_visitor_centres_inform():
    # Saimaa Geopark visitor center (9b1b77ec).
    for name in ("Saimaa Geopark visitor center", "Saimaa Geopark visitor centre"):
        category, extra = cat(make_spider(), name)
        assert category == Categories.TOURISM_INFORMATION
        assert extra == {"information": "visitor_centre"}


def test_dog_yards_are_dog_parks():
    assert cat(make_spider(), "Koiratarha")[0] == Categories.LEISURE_DOG_PARK
    assert cat(make_spider(), "Södra familjedagvårdsområden")[0] == Categories.KINDERGARTEN
    assert cat(make_spider(), "Helsingin yhteislyseo")[0] == Categories.SCHOOL


def test_premise_units_split():
    # Kielotie 42 asunnot 1-4 (b8c6383d): lowercase premise words split too.
    item = addressed(make_spider(), "Kielotie", "42 asunnot 1-4", postcode="01300", office="VANTAA")
    assert item["street"] == "Kielotie"
    assert item["housenumber"] == "42"
    assert item["extras"].get("addr:unit") == "asunnot 1-4"


def test_slash_venue_tails_name_poi():
    spider = make_spider()
    assert split(spider, "Hyvät Tuulet ry/MyöhäTuulen kohtaamispaikka") == (
        "MyöhäTuulen kohtaamispaikka",
        None,
        "Hyvät Tuulet ry/MyöhäTuulen kohtaamispaikka",
    )
    assert split(spider, "Harjulan Setlementti ry/Kansalaisopisto") == (
        "Kansalaisopisto",
        None,
        "Harjulan Setlementti ry/Kansalaisopisto",
    )
    assert split(spider, "Harjulan Setlementti ry/Liikuntapalvelut") == (
        "Harjulan Setlementti ry",
        None,
        "Harjulan Setlementti ry/Liikuntapalvelut",
    )
    assert cat(spider, "Kansalaisopisto")[0] == Categories.COLLEGE


def test_space_city_brands_and_activities():
    spider = make_spider()
    assert split(spider, "SavoGrow Pielavesi", "Pielavesi") == ("SavoGrow Pielavesi", None, None)
    assert split(spider, "Avoin jumpparyhmä Kouvola", "Kouvola") == (
        "Avoin jumpparyhmä",
        None,
        "Avoin jumpparyhmä Kouvola",
    )


def test_operator_tail_venues_drop():
    # Löytöeläimet Eura (60cff49b): association tail is no venue.
    item = parsed(make_spider(), channel("Löytöeläimet Eura, Säkylä ja Rauma / Eläinten hyväksi EHY ry"))
    assert item["name"] == "Löytöeläimet Eura, Säkylä ja Rauma"
    assert item.get("located_in") is None
    assert item["extras"]["amenity"] == "animal_shelter"


def test_paren_venue_lists_locate():
    # Hansakallion units (7de02537): proper-name lists locate the POI.
    signed = "Hansakallion ympärivuorokautinen asumispalvelu (Masto, Styyrpuuri,Vantti)"
    item = parsed(make_spider(), channel(signed))
    assert item["name"] == "Hansakallion ympärivuorokautinen asumispalvelu"
    assert item["located_in"] == "Masto, Styyrpuuri, Vantti"
    assert item["extras"]["official_name"] == signed


def test_multi_venue_heads_keep_all():
    # Riihikoti, Villava (a2fe8ab0): no venue is eaten as a city tail.
    item = parsed(make_spider(), channel("Riihikoti, Villava, ikäihmisten asumispalvelut", office="RIIHIMÄKI"))
    assert item["name"] == "Ikäihmisten asumispalvelut"
    assert item["located_in"] == "Riihikoti, Villava"


def test_service_descriptor_tails_drop():
    # Teuvolan vammaisten asumispalvelut (4ac9bfce): services don't locate.
    item = parsed(
        make_spider(),
        channel("Teuvolan vammaisten asumispalvelut, tilapäishoito ja loma-ajanhoito, Forssa", office="FORSSA"),
    )
    assert item["name"] == "Teuvolan vammaisten asumispalvelut"
    assert item.get("located_in") is None


def test_school_hosted_groups_locate():
    # Lempeä selkäjooga-ryhmä (f46f7e7e): generic activity at its school.
    item = parsed(make_spider(), channel("Lempeä selkäjooga-ryhmä, Veittijärven koulu -palvelun järjestämispaikka"))
    assert item["name"] == "Lempeä selkäjooga-ryhmä"
    assert item["located_in"] == "Veittijärven koulu"
    assert item.get_tag("amenity") == "yes"


def test_care_rescue_skips_activity_names():
    # Nakkifiesta (601455b7): mental-health ontology describes purpose.
    spider = make_spider()
    ch = channel("Nakkifiesta")
    ch["services"] = [{"service": {"name": "Nakkifiesta"}}]
    ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": "mielenterveys"}]}]
    assert parsed(spider, ch).get_tag("amenity") == "yes"


def test_memorial_translations_rescue():
    # Mortuis (980f0c61): sv/en memorial names type the opaque one.
    spider = make_spider()
    ch = channel("Mortuis")
    ch["serviceChannelNames"] = [
        {"language": "fi", "value": "Mortuis", "type": "Name"},
        {"language": "sv", "value": "Mortius, minnesmärke över explosionen", "type": "Name"},
        {"language": "en", "value": "Mortuis memorial", "type": "Name"},
    ]
    item = parsed(spider, ch)
    assert item.get_tag("tourism") == "artwork"
    assert "place" not in item["extras"]


def test_competence_centre_rescues_social():
    # Osaamiskeskus, Pietarsaari (dff872d6): no island tag on venues.
    spider = make_spider()
    ch = channel("Osaamiskeskus, Pietarsaari")
    ch["services"] = [{"service": {"name": "Osaamiskeskus"}}]
    ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": "kehitysvammaiset"}]}]
    item = parsed(spider, ch)
    assert item.get_tag("amenity") == "social_facility"
    assert "place" not in item["extras"]


def test_coordinate_tails_strip():
    spider = make_spider()
    assert spider._clean_name("Mustasaari, P 60° 10,343' ja I 24° 52,123'") == "Mustasaari"
    assert spider._clean_name("Seurasaari, 60°10'52'N, 024°53'05'E") == "Seurasaari"


def test_pobox_roads_drop():
    # Tyks T-sairaala (db72a7ee): "PL 52" is no street.
    item = Feature()
    make_spider()._apply_address(
        item,
        {
            "street": [{"language": "fi", "value": "Pl 52"}],
            "streetNumber": "",
            "postalCode": "20520",
            "postOffice": [{"language": "fi", "value": "TURKU"}],
        },
        "20520",
        "Turku",
    )
    assert item.get("street") is None
    assert item.get("housenumber") is None
    assert item["postcode"] == "20520"


def test_postcode_units_drop():
    # Varikko (413aecc1): the postcode is never a unit.
    item = Feature()
    make_spider()._apply_address(
        item,
        {
            "street": [{"language": "fi", "value": "Varastotie 4"}],
            "streetNumber": "67100",
            "postalCode": "67100",
            "postOffice": [{"language": "fi", "value": "KOKKOLA"}],
        },
        "67100",
        "Kokkola",
    )
    assert item["street"] == "Varastotie"
    assert item.get("extras", {}).get("addr:unit") is None


def test_foundation_operators_are_private():
    item = parsed(make_spider(), channel("Viherlaakson asumispalveluyksikkö", org="Mente säätiö sr"), "Mente säätiö sr")
    assert item["extras"].get("operator:type") == "private"


def test_operator_brand_suffixes():
    spider = make_spider()
    item = parsed(spider, channel("TestPlace"), "Pohjois-Karjalan hyvinvointialue – Siun sote")
    assert item["operator"] == "Pohjois-Karjalan hyvinvointialue"
    assert item["extras"].get("operator:type") is None
    item = parsed(spider, channel("TestPlace"), "Brottsofferjouren - RIKU")
    assert item["operator"] == "Brottsofferjouren"
    assert item["extras"].get("operator:type") == "private"
    item = parsed(spider, channel("TestPlace"), "FinFami - Uusimaa ry")
    assert item["operator"] == "FinFami - Uusimaa ry"
    assert item["extras"].get("operator:type") == "private"


def test_hobby_and_culture_centres():
    spider = make_spider()
    assert cat(spider, "Hyvinvointi- ja harrastuskeskus")[0] == Categories.COMMUNITY_CENTRE
    assert cat(spider, "Hervannan yhteisökeskus")[0] == Categories.COMMUNITY_CENTRE
    assert cat(spider, "Kulttuuritila Näkkäri")[0] == Categories.COMMUNITY_CENTRE
    assert cat(spider, "Rulla")[0] is None
    assert cat(spider, "Lastenkulttuurikeskus")[0] == Categories.ARTS_CENTRE
    assert cat(spider, "Taiteen perusopetus")[0] == Categories.ARTS_CENTRE
    assert cat(spider, "Kuvataidekoulu")[0] == Categories.SCHOOL


def test_city_housing_services_desk():
    # Oriveden kaupungin asumispalvelut (af9ea7a6): municipal desks stay offices.
    assert cat(make_spider(), "Oriveden kaupungin asumispalvelut")[0] == Categories.OFFICE_GOVERNMENT


def test_addiction_care_is_clinic():
    spider = make_spider()
    assert cat(spider, "Opioidiriippuvaisten korvaushoito")[0] == Categories.CLINIC
    assert cat(spider, "Päihdevieroitus")[0] == Categories.CLINIC


def test_psychiatric_hospitals_are_hospitals():
    assert cat(make_spider(), "Kymenlaakson psykiatrinen sairaala")[0] == Categories.HOSPITAL


def test_pool_halls_have_swimming():
    category, extra = cat(make_spider(), "Uimahalli")
    assert category == Categories.LEISURE_SPORTS_CENTRE
    assert extra == {"sport": "swimming"}


def test_reuse_stations_are_recycling():
    assert cat(make_spider(), "Taavetin Hyödyksi-asema")[0] == Categories.RECYCLING


def test_resident_premises_are_community():
    assert cat(make_spider(), "Etappi yhteisötila")[0] == Categories.COMMUNITY_CENTRE


def test_multipurpose_rooms_are_community():
    assert cat(make_spider(), "Joutsenon kirjaston monitoimitila Olkkari")[0] == Categories.COMMUNITY_CENTRE


def test_supported_housing_is_assisted():
    assert cat(make_spider(), "Matinniitty tuettu asuminen")[0] == Categories.ASSISTED_LIVING


def test_elderly_housing_carries_for_senior():
    item = parsed(make_spider(), channel("Ikäihmisten asumispalvelut"))
    assert item.get_tag("amenity") == "social_facility"
    assert item["extras"].get("social_facility:for") == "senior"


def test_climbing_spots():
    category, extra = cat(make_spider(), "Seikkailutalon piha-alueen kiipeilypisteet")
    assert category == Categories.LEISURE_PITCH
    assert extra == {"sport": "climbing"}


def test_island_markers():
    spider = make_spider()
    assert cat(spider, "Malkasaari (saari)")[1] == {"place": "island"}
    assert cat(spider, "Kotiluoto (saari)")[1] == {"place": "island"}
    assert cat(spider, "Tiirakari (saari)")[1] == {"place": "island"}


def test_winter_swimmers():
    spider = make_spider()
    assert cat(spider, "Ourit (Talviuimarit)")[0] == Categories.LEISURE_SWIMMING_AREA
    assert cat(spider, "Talviuimaranta")[0] == Categories.LEISURE_SWIMMING_AREA


def test_youth_homes_are_group_homes():
    spider = make_spider()
    assert cat(spider, "Rovaniemen Etelärinteen lapsi- ja nuorisokoti")[1] == {"social_facility": "group_home"}
    assert cat(spider, "Sonkajärven kotiseututalo")[0] == Categories.COMMUNITY_CENTRE


def test_company_office_genitive():
    assert cat(make_spider(), "Mikkelin Asumisoikeus Oy:n toimisto")[0] == Categories.OFFICE_COMPANY


def test_venue_tails_keep_house():
    # Pertunmaa-talo (57c60fa7): hyphenated house compounds stay whole.
    item = parsed(make_spider(), channel("Pertunmaa-talo"))
    assert item["name"] == "Pertunmaa-talo"


def test_island_head_venues_split():
    # Kaunissaari camping (9ddfc82f): facility names, island locates.
    name, located, official = split(make_spider(), "Kaunissaari / Telttailu- ja leiriytymispaikka 2.")
    assert name == "Telttailu- ja leiriytymispaikka 2."
    assert located == "Kaunissaari"


def test_operator_tail_names_operator():
    # Imatra Bowling Center: tail company operates, located stays null.
    item = parsed(
        make_spider(),
        channel("Imatra Bowling Center / Imatran keilahalli Oy"),
        "Imatran kaupunki",
    )
    assert item["name"] == "Imatra Bowling Center"
    assert item.get("located_in") is None
    assert item["operator"] == "Imatran keilahalli Oy"
    assert item["extras"].get("operator:type") == "private"


def test_venue_head_with_city_tail_splits():
    # Kivari, Riihimäki (70f3e324): proper venue heads resolve their city.
    item = parsed(make_spider(), channel("Kivari, Riihimäki, Vammaisten asumispalvelut", office="RIIHIMÄKI"))
    assert item["name"] == "Vammaisten asumispalvelut"
    assert item["located_in"] == "Kivari"


def test_compound_facility_slash_keeps_whole():
    # Ikifit Keinupuisto/Hilpi (8a345091): facility compounds don't split.
    item = parsed(
        make_spider(),
        channel(
            "Ikifit Oy, hyvinvointikeskus Keinupuisto/Hilpi, Hämeenlinna, yhteisöllisen asumisen ostopalvelut",
            office="HÄMEENLINNA",
        ),
    )
    assert item["name"] == "Ikifit Oy, hyvinvointikeskus Keinupuisto/Hilpi"
    assert item.get("located_in") is None


def test_olka_desks_are_offices():
    # OLKA-pisteiltä (d8fb52c1): desks, not association houses.
    assert cat(make_spider(), "OLKA-pisteiltä tietoa yhdistysten toiminnasta")[0] == (Categories.OFFICE_GOVERNMENT)


def test_youth_care_services_are_clinics():
    spider = make_spider()
    assert cat(spider, "Konneveden, Uuraisten ja Äänekosken nuorten mielenterveys- ja päihdetyön tiimi")[0] == (
        Categories.CLINIC
    )
    assert cat(spider, "Nuorten päihdepalvelu Pysäkki")[0] == Categories.CLINIC
    assert cat(spider, "Lasten ja nuorten mielenterveyspalvelut")[0] == Categories.CLINIC
    assert cat(spider, "Nuorisoasema")[0] == Categories.OFFICE_GOVERNMENT


def test_police_desk_splits_to_service():
    # Äänekosken poliisiasema, lupapalvelut: desk names, station locates.
    spider = make_spider()
    item = parsed(spider, channel("Äänekosken poliisiasema, lupapalvelut", office="ÄÄNEKOSKI"))
    assert item["name"] == "Lupapalvelut"
    assert item["located_in"] == "Äänekosken poliisiasema"
    assert item.get_tag("office") == "government"
    assert cat(spider, "Poliisiasema")[0] == Categories.POLICE


def test_ward_names_cap_rescue_at_clinic():
    # Raaseporin TK vuodeosasto (b43f874c): hospital ontology doesn't outrank the ward.
    spider = make_spider()
    ch = channel("Raaseporin TK vuodeosasto")
    ch["services"] = [{"service": {"name": "Perustason osastohoito"}}]
    ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": "sairaalat"}]}]
    assert parsed(spider, ch).get_tag("amenity") == "clinic"


def test_city_prefix_only_strips_services():
    # Salo-Karinan neuvonta-asema: proper compounds stay whole.
    item = parsed(make_spider(), channel("Salo-Karinan neuvonta-asema", office="SALO"))
    assert item["name"] == "Salo-Karinan neuvonta-asema"
    assert item.get_tag("office") == "government"


def test_sorting_stations_are_recycling():
    # LSJH Perniön lajitteluasema: no railway station.
    spider = make_spider()
    assert cat(spider, "Perniön lajitteluasema")[0] == Categories.RECYCLING
    # Dagsmarkin lainausasema: lending station, not railway.
    assert cat(spider, "Dagsmarkin " + "laina" + "usasema")[0] == Categories.LIBRARY
    assert cat(spider, "Lentoaseman rautatieasema")[1] == {"railway": "station", "public_transport": "station"}


def test_sheep_pens_are_attractions():
    assert cat(make_spider(), "Koivuhaan lammasaitaus")[0] == Categories.TOURISM_ATTRACTION


def test_mediation_service_name_kept():
    # Rikos -ja riita-asioiden sovittelua: suffix strips, remainder stays.
    signed = "Rikos -ja riita-asioiden sovittelua -palvelun järjestämispaikka"
    item = parsed(make_spider(), channel(signed))
    assert item["name"] == "Rikos -ja riita-asioiden sovittelua"
    assert item["extras"]["official_name"] == signed
    assert cat(make_spider(), "Elinkeinopalvelut")[0] == Categories.OFFICE_GOVERNMENT


def test_screenings_and_exam_units_are_clinics():
    spider = make_spider()
    assert cat(spider, "Kohdunkaulan syövän seulonta")[0] == Categories.CLINIC
    assert cat(spider, "Sikiöseulonnat")[0] == Categories.CLINIC
    assert cat(spider, "Sikiötutkimusyksikkö")[0] == Categories.CLINIC
    assert cat(spider, "Tutkimusyksiköt, toimipisteet")[0] == Categories.CLINIC
    # Screening hosted by a hospital files as the screening unit.
    assert cat(spider, "Rintasyöpäseulonta Oulun yliopistollisessa sairaalassa")[0] == Categories.CLINIC


def test_rehab_guidance_is_social():
    spider = make_spider()
    assert cat(spider, "Kuntoutusohjaus- ja asiantuntijapalvelut")[0] == Categories.SOCIAL_FACILITY
    # Kolpeneen tuki- ja osaamiskeskus (9e7d7841) rescues via its service.
    ch = channel("Kolpeneen tuki- ja osaamiskeskus")
    ch["services"] = [{"service": {"name": "Kuntoutusohjaus- ja asiantuntijapalvelut"}}]
    assert parsed(spider, ch).get_tag("amenity") == "social_facility"


def test_disability_services_are_social():
    # OYS Konsti (45f088c7) rescues via Vaativat kehitysvammapalvelut.
    spider = make_spider()
    assert cat(spider, "Vaativat kehitysvammapalvelut")[0] == Categories.SOCIAL_FACILITY
    ch = channel("OYS Konsti")
    ch["services"] = [{"service": {"name": "Vaativat kehitysvammapalvelut"}}]
    assert parsed(spider, ch).get_tag("amenity") == "social_facility"


def test_service_desks_rescue_offices():
    # Pirtin Kohtaamo (4ed0941b): opaque name, desk-shaped services.
    spider = make_spider()
    ch = channel("Pirtin Kohtaamo")
    ch["services"] = [
        {"service": {"name": "Kunnan viralliset ilmoitukset"}},
        {"service": {"name": "Asiakaspalvelu"}},
        {"service": {"name": "Kelan asiointipiste Pudasjärvellä"}},
    ]
    assert parsed(spider, ch).get_tag("office") == "government"


def test_place_description_beats_desk_label():
    # A care home with a customer-service desk still files by place
    # (assisted_living renders as amenity=social_facility).
    from locations.items import Feature

    spider = make_spider()
    ch = channel("Maya", descriptions=[{"language": "fi", "value": "Ikääntyvien asumispalveluyksikkö"}])
    ch["services"] = [{"service": {"name": "Asiakaspalvelu"}}]
    assert spider._resolve_fallback_category(Feature(), ch) == Categories.ASSISTED_LIVING


def test_event_houses_are_venues():
    assert cat(make_spider(), "Tapahtumatalo")[0] == Categories.EVENTS_VENUE


def test_camp_areas_are_camp_sites():
    spider = make_spider()
    assert cat(spider, "Lankarin leirikeskuksen pururata")[0] == Categories.TOURISM_CAMP_SITE
    assert cat(spider, "Vuolahden leirialue")[0] == Categories.TOURISM_CAMP_SITE
    assert cat(spider, "Rastilan leirintäalue")[0] == Categories.TOURISM_CAMP_SITE


def test_animal_protection_desk_is_office():
    spider = make_spider()
    assert cat(spider, "Eläinsuojelu")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Porvoon kissatalo")[1] == {"amenity": "animal_shelter"}


def test_depots_are_depots():
    spider = make_spider()
    assert cat(spider, "Kunnanvarikko")[1] == {"amenity": "depot"}
    assert cat(spider, "Vantaan kaupungin varikko")[1] == {"amenity": "depot"}
    # Venues named after depots keep their filings.
    assert cat(spider, "Nuorisotila Varikko")[1] == {"amenity": "youth_centre"}
    assert cat(spider, "Varikkotien leikkikenttä")[0] == Categories.LEISURE_PLAYGROUND


def test_chain_daycares():
    # Pilke Kilonkallio (6781665c), Norlandia Kärry (048c0165): brand heads
    # type the unit and name the private operator over the purchaser city.
    spider = make_spider()
    for name, brand in (("Pilke Kilonkallio", "Pilke"), ("Norlandia Kärry", "Norlandia")):
        assert cat(spider, name)[0] == Categories.KINDERGARTEN
        item = parsed(spider, channel(name), "Espoon kaupunki")
        assert item["operator"] == brand
        assert item["extras"].get("operator:type") == "private"


def test_aviation_centre_is_aerodrome():
    # Pudasjärven Ilmailukeskus (29789472), on Lentäjäntie.
    assert cat(make_spider(), "Pudasjärven Ilmailukeskus")[1] == {"aeroway": "aerodrome"}


def test_airport_desks_are_not_railway():
    spider = make_spider()
    assert cat(spider, "Asiakaspalvelupisteet Helsinki-Vantaan lentoasemalla")[0] == (Categories.OFFICE_GOVERNMENT)
    assert cat(spider, "Lentoaseman rautatieasema")[1] == {"railway": "station", "public_transport": "station"}


def test_combined_boat_harbour_is_marina():
    spider = make_spider()
    assert cat(spider, "Sirkkakosken vene- ja kalasatama")[0] == Categories.MARINA
    assert cat(spider, "Kalasatama")[0] is None


def test_culture_houses_are_community():
    assert cat(make_spider(), "Kulttuuritalo Kimara")[0] == Categories.COMMUNITY_CENTRE


def test_cemeteries_are_cemeteries():
    spider = make_spider()
    assert cat(spider, "Pieneläinten hautausmaa")[1] == {"landuse": "cemetery"}
    assert cat(spider, "Pieneläinhautausmaa")[1] == {"landuse": "cemetery"}
    # Offices and chapels at cemeteries keep their filings.
    assert cat(spider, "Riihimäen hautausmaan toimisto")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Lepolan hautausmaan kappeli")[0] == Categories.PLACE_OF_WORSHIP


def test_english_gym_is_fitness_centre():
    spider = make_spider()
    assert cat(spider, "Sportis gym")[0] == Categories.GYM
    assert cat(spider, "Fitness Center")[0] == Categories.GYM
    assert cat(spider, "Gymnasium")[0] == Categories.SCHOOL
    assert cat(spider, "Gymnasiet i Petalax")[0] == Categories.SCHOOL


def test_brand_city_kept():
    # International House Rauma (4a7e76d8): the city is part of the brand.
    assert split(make_spider(), "International House Rauma", "Rauma") == ("International House Rauma", None, None)


def test_boilerplate_leaves_service_name():
    # Näe hyvä mussa -leirit lapsille (c096c655): only the suffix strips.
    item = parsed(make_spider(), channel("Näe hyvä mussa -leirit lapsille -palvelun järjestämispaikka, 1"))
    assert item["name"] == "Näe hyvä mussa -leirit lapsille"
    assert item["extras"]["official_name"] == "Näe hyvä mussa -leirit lapsille -palvelun järjestämispaikka, 1"


def test_playgroups_are_kindergartens():
    spider = make_spider()
    assert cat(spider, "Pääskyvuoren leikkikerho")[0] == Categories.KINDERGARTEN
    assert cat(spider, "Leikkikoulu")[0] == Categories.KINDERGARTEN


def test_swedish_daycare_name_rescues():
    # Daghemmet Karitsa (6e910728): the Swedish name types the opaque one.
    ch = channel("Karitsa")
    ch["serviceChannelNames"] = [
        {"language": "fi", "value": "Karitsa", "type": "Name"},
        {"language": "sv", "value": "Daghemmet Karitsa", "type": "Name"},
    ]
    assert parsed(make_spider(), ch).get_tag("amenity") == "kindergarten"


def test_service_desk_swedish_and_nurse_rows():
    spider = make_spider()
    assert cat(spider, "Pargas serviceenhet")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Diabeteshoitaja, Kaarina")[1] == {"healthcare": "nurse"}
    assert cat(spider, "Kaarinan kaupungin rakennusvalvonnan lupa-asiat")[0] == (Categories.OFFICE_GOVERNMENT)


def test_bare_operator_unit_names_unit():
    # Sateenkaari Koto Oy/ Villasukka: the proper unit names the POI,
    # the company is the operator, never the name.
    name, located, official = split(make_spider(), "Sateenkaari Koto Oy/ Villasukka")
    assert name == "Villasukka"
    assert located is None
    assert official == "Sateenkaari Koto Oy/ Villasukka"


def test_apoteket_is_pharmacy():
    # Apoteket (the pharmacy, in Swedish) files like apteekki.
    assert cat(make_spider(), "Apoteket")[0] == Categories.PHARMACY


def test_official_name_wins_over_alternative():
    # "Talaskangas" (AlternativeName) must lose to "Talaskankaan
    # retkeilyreitti" (Name): suomi.fi renders per displayNameType.
    spider = make_spider()
    ch = channel("Talaskangas")
    ch["serviceChannelNames"] = [
        {"language": "fi", "value": "Talaskangas", "type": "AlternativeName"},
        {"language": "fi", "value": "Talaskankaan retkeilyreitti", "type": "Name"},
    ]
    ch["displayNameType"] = [{"type": "Name", "language": "fi"}]
    assert spider._names(ch)["fi"] == "Talaskankaan retkeilyreitti"


# ---- Review round 6: operator and contact -------------------------------------


def test_association_demote_end_to_end():
    from locations.items import Feature as _F
    from locations.categories import apply_category as _apply

    spider = make_spider()
    item = _F()
    _apply(Categories.OFFICE_GOVERNMENT, item)
    spider._apply_operator(item, "Pirkanmaan Sydänyhdistys ry")
    assert item["extras"]["office"] == "association"
    assert item["extras"]["operator:type"] == "private"


def test_dotted_and_bare_operator_markers():
    spider = make_spider()
    assert spider._has_operator_word("Al-Anon Keskuspalvelu r.y.") is True
    assert spider._has_operator_word("Barnavårdsföreningen i Finland r.f.") is True
    assert spider._has_operator_word("Tmi Petri Lehto") is True
    assert spider._is_private_org("Palvelualojen Työttömyyskassa") is True
    assert spider._has_operator_word("Derby") is False
    assert spider._is_private_org("Suomen Punainen Risti Kuopion osasto") is True
    assert spider._is_private_org("SANL ry / Luetaan yhdessä -verkosto") is True
    assert spider._is_private_org("Keravan kansantanssijat") is True
    assert spider._is_private_org("Attendo") is True
    assert spider._is_private_org("Helsingin kaupunki") is False


def test_placeholder_email_dropped():
    from locations.items import Feature as _F

    spider = make_spider()
    item = _F()
    spider._apply_contact(item, {"emails": [{"value": "etunimi.sukunimi@kalajoki.fi"}]})
    assert "email" not in item


def test_menu_host_dropped():
    from locations.items import Feature as _F

    spider = make_spider()
    item = _F()
    spider._apply_contact(item, {"webPages": [{"url": "https://menu.kaarea.fi/KaareaAromieMenus/FI/Default"}]})
    assert "website" not in item


def test_translations_always_name_lang():
    spider = make_spider()
    item = parsed(
        spider,
        channel("Laboratorio, Taivassalo", office="TAIVASSALO", sv="Tykslab"),
        "Turun yliopistollinen keskussairaala",
    )
    assert item["extras"]["name:sv"] == "Tykslab"
    assert item["extras"].get("official_name:sv") is None
    item = parsed(spider, channel("Myllypuron liikuntapuisto", en="Myllypuro sports park 1*"), "Helsingin kaupunki")
    assert item["extras"]["name:en"] == "Myllypuro sports park"


# ---- Review round 7: categories ------------------------------------------------


def test_health_service_rows():
    spider = make_spider()
    assert cat(spider, "Sevettijärven terveystalo")[0] == Categories.CLINIC
    assert cat(spider, "Lapin keskussairaalan laboratorio") == (
        Categories.CLINIC,
        {"healthcare": "laboratory"},
    )
    assert cat(spider, "Happy Toddlers")[0] == Categories.KINDERGARTEN
    assert cat(spider, "Daycare Daisy Oy")[0] == Categories.KINDERGARTEN
    assert cat(spider, "Kaupunkitila- ja maisemasuunnittelu")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Stadshus")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Sähköauton latauspiste")[0] == Categories.CHARGING_STATION
    assert cat(spider, "Juhannussalko")[0] == Categories.TOURISM_ARTWORK
    assert cat(spider, "Koulun piha")[0] == Categories.SCHOOL
    assert cat(spider, "Kirkonkylän kylätalo")[0] == Categories.COMMUNITY_CENTRE
    assert cat(spider, "Auditorio")[0] == Categories.EVENTS_VENUE
    assert cat(spider, "Kuulolähipalvelu")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Sammontalon päiväkodin Uus-Lavolan toimintayksikkö")[0] == Categories.KINDERGARTEN


def test_service_tail_substring_inversion():
    # Plural service tails invert like singulars (Hoitoalan ruokapalvelut).
    name, located, official = split(make_spider(), "Koskelan monipuolinen palvelukeskus / Hoitoalan ruokapalvelut")
    assert name == "Hoitoalan ruokapalvelut"
    assert located == "Koskelan monipuolinen palvelukeskus"
    assert official == "Koskelan monipuolinen palvelukeskus / Hoitoalan ruokapalvelut"
    assert cat(make_spider(), "Koskelan monipuolinen palvelukeskus / Hoitoalan ruokapalvelut")[0] == (
        Categories.CANTEEN
    )


def test_fishing_spot_facility():
    spider = make_spider()
    assert cat(spider, "Salmen ulkoilualue / Kalastuspaikka")[1] == {"leisure": "fishing"}
    name, located, _ = split(spider, "Salmen ulkoilualue (Pikku-Parikas) / Kalastuspaikka")
    assert name == "Kalastuspaikka"
    assert located == "Salmen ulkoilualue (Pikku-Parikas)"


def test_paren_address_strips_english_names():
    # Daycare Daisy Oy (Ylioppilaskatu 25): the sample row predates the
    # fix; current code strips the address paren (verified live).
    assert split(make_spider(), "Daycare Daisy Oy (Ylioppilaskatu 25)")[0] == "Daycare Daisy Oy"


def test_always_open_skipped_for_schools():
    spider = make_spider()
    channel = {
        "serviceHours": [
            {
                "serviceHourType": "DaysOfTheWeek",
                "isAlwaysOpen": True,
                "openingHour": [{"dayFrom": "Monday", "dayTo": "Sunday", "from": "00:00:00", "to": "23:59:59"}],
            }
        ]
    }
    assert spider._hours(channel, Categories.SCHOOL) is None
    assert spider._hours(channel, Categories.KINDERGARTEN) is None


def test_closed_only_hours_emit_no_tag():
    # Closed-only sets render empty: no opening_hours key, never "".
    spider = make_spider()
    ch = channel("Suljettu piste")
    ch["serviceHours"] = [
        {
            "serviceHourType": "DaysOfTheWeek",
            "isClosed": True,
            "openingHour": [{"dayFrom": "Monday", "dayTo": "Monday"}],
        }
    ]
    item = parsed(spider, ch)
    assert "opening_hours" not in item
    assert "opening_hours" not in (item.get("extras") or {})


# ---- Review rounds 8-10: names, categories, addresses -------------------------


def test_office_desk_pair_stays_whole():
    # Keurusselän joint office + Mänttä-Vilppula desk: Stadin rule for
    # offices (schools still split hosted units).
    name, located, official = split(
        make_spider(), "Keurusselän ympäristön- ja terveydensuojelutoimisto / Mänttä-Vilppulan toimipiste"
    )
    signed = "Keurusselän ympäristön- ja terveydensuojelutoimisto / Mänttä-Vilppulan toimipiste"
    assert (name, located, official) == (signed, None, None)


def test_fused_school_splits_anchored():
    spider = make_spider()
    name, located, official = split(spider, "Renkomäen koulun vaativan monimuotoisen tuen luokat")
    assert name == "Vaativan monimuotoisen tuen luokat"
    assert located == "Renkomäen koulu"
    assert official == "Renkomäen koulun vaativan monimuotoisen tuen luokat"


def test_swedish_school_concatenation_kept_whole():
    # Swedish "<Place> skolan <facility>" heads ("Helsinge skolan
    # liikuntasali", "Lagstads skolan liikuntasali 2") stay whole:
    # splitting would glue a genitive place to a de-inflected skola,
    # inventing a venue ("Lagstads skola") that appears nowhere.
    spider = make_spider()
    for signed in ("Helsinge skolan liikuntasali", "Lagstads skolan liikuntasali 2"):
        assert split(spider, signed) == (signed, None, None), signed


def test_dash_school_kept_whole():
    # A school housed inside itself is one name, not a hosted unit.
    signed = "Kaukajärven koulu - Annalan koulutalo"
    assert split(make_spider(), signed) == (signed, None, None)


def test_kela_in_name_names_provider():
    from locations.items import Feature as _F

    spider = make_spider()
    assert spider._branch_agency("Kelan asiointipiste Lapinlahdella") == "Kela"
    assert spider._branch_agency("Kelankatu 1") is None
    assert spider._branch_agency("Siimakela") is None
    item = parsed(spider, channel("Kelan asiointipiste Lapinlahdella"), "Lapinlahden kunta")
    assert item["operator"] == "Kela"


def test_seurakunta_operator_public():
    from locations.items import Feature as _F
    from locations.categories import apply_category as _apply

    spider = make_spider()
    # Parishes are public-law bodies, not associations.
    assert spider._is_private_org("Kirkkonummen suomalainen seurakunta") is False
    assert spider._is_private_org("Helsingin vapaaseurakunta ry") is True
    item = _F()
    _apply(Categories.OFFICE_GOVERNMENT, item)
    spider._apply_operator(item, "Parikkalan seurakunta")
    assert item["operator"] == "Parikkalan seurakunta"
    assert item["extras"].get("office") == "government"
    assert item["extras"].get("operator:type") == "religious"


def test_acronym_unit_is_clinic():
    spider = make_spider()
    assert cat(spider, "Vatsakeskus, Tays Hatanpää")[0] == Categories.CLINIC
    assert cat(spider, "Vaativa kuntoutusyksikkö, Tays Hatanpää")[0] == Categories.CLINIC
    assert cat(spider, "Arviointiyksikkö")[0] == Categories.CLINIC


def test_service_desk_office_rows():
    spider = make_spider()
    assert cat(spider, "Mittauspalvelut")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Sisäinen tarkastus")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Terveyspalvelut")[0] == Categories.CLINIC  # terveyspalvelu outranks palvelut
    assert cat(spider, "Iisalmen poliisiasema")[0] == Categories.POLICE  # police outranks tarkastus


def test_plural_fields_normalize():
    spider = make_spider()
    assert cat(spider, "Tenniskentät") == (Categories.LEISURE_PITCH, {"sport": "tennis"})
    assert cat(spider, "Kangaslammin nurmikentät")[0] == Categories.LEISURE_PITCH


def test_beach_volley_spaced():
    spider = make_spider()
    for fi in (
        "Tikkakosken liikuntapuiston beach volley -kenttä",
        "Velaatan uimarannan beach volley -kenttä",
    ):
        category, extra = cat(spider, fi)
        assert category == Categories.LEISURE_PITCH, fi
        assert extra["sport"] == "beachvolleyball", fi


def test_apartment_abbr_unit():
    item = addressed(make_spider(), "Oikopolku", "2 as 3")
    assert (item["street"], item["housenumber"]) == ("Oikopolku", "2")
    assert "street_address" not in item
    assert item["extras"]["addr:unit"] == "as 3"


def test_numeric_dup_unit_dropped():
    item = addressed(make_spider(), "Katu", "51, 51")
    assert (item["street"], item["housenumber"]) == ("Katu", "51")
    assert "street_address" not in item
    assert "addr:unit" not in item["extras"]


def test_nimi_placeholder_email_dropped():
    from locations.items import Feature as _F

    spider = make_spider()
    item = _F()
    spider._apply_contact(item, {"emails": [{"value": "nimi.sukunimi@kunta.fi"}]})
    assert "email" not in item


def test_island_area_tails_locate():
    # Island service areas locate the POI instead of dropping the island.
    name, located, official = split(make_spider(), "Kahvila / Ulkoilusaari")
    assert name == "Kahvila"
    assert located == "Ulkoilusaari"
    assert official == "Kahvila / Ulkoilusaari"


# ---- Review rounds 9-11: remaining categories ---------------------------------


def test_zoo_athletics_gallery_shops():
    spider = make_spider()
    assert cat(spider, "Korkeasaaren eläintarha")[1] == {"tourism": "zoo"}
    assert cat(spider, "Yli-Iin yleisurheilukeskus") == (
        Categories.LEISURE_SPORTS_CENTRE,
        {"sport": "athletics"},
    )
    assert cat(spider, "Yleisurheilukenttä")[0] == Categories.LEISURE_TRACK
    assert cat(spider, "Raatihuone, raatihuonegalleria")[0] == Categories.ARTS_CENTRE
    assert cat(spider, "Roihupellon myymälä, Stadin ammattiopisto")[1] == {"shop": "yes"}
    assert cat(spider, "Lahden kaupunginteatterin lippumyymälä")[1] == {"shop": "tickets"}


def test_stations():
    spider = make_spider()
    assert cat(spider, "Vehkalan asema")[1] == {"railway": "station", "public_transport": "station"}
    assert cat(spider, "Linja-autoasema")[0] == Categories.BUS_STATION
    assert cat(spider, "Huoltoasema")[0] is None
    assert cat(spider, "Paloasema")[0] == Categories.FIRE_STATION


def test_youth_and_wards_swedish():
    spider = make_spider()
    assert cat(spider, "Sökö ungdomslokal")[1] == {"amenity": "youth_centre"}
    assert cat(spider, "Geriatrinen akuuttiosasto")[0] == Categories.CLINIC
    assert cat(spider, "Oulun lyhytaikaishoidon yksikkö Elviira")[0] == Categories.NURSING_HOME


def test_service_desk_rows():
    spider = make_spider()
    assert cat(spider, "Mittauspalvelut")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Sisäinen tarkastus")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Työllistymistä edistävä monialainen palvelu TYM")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Iisalmen poliisiasema")[0] == Categories.POLICE


def test_roihuvara_day_unit_and_star():
    # Bare-slash day-activity unit inverts; the rating star drops in cleaning.
    name, located, official = named(make_spider(), "Roihuvuoren seniorikeskus/Liina päivätoiminta 2*", "Helsinki")
    assert name == "Liina päivätoiminta 2"
    assert located == "Roihuvuoren seniorikeskus"
    assert official == "Roihuvuoren seniorikeskus/Liina päivätoiminta 2"


def test_suomenlinna_fishing_inverts():
    name, located, _ = split(make_spider(), "Suomenlinna / Kalastuspaikka")
    assert name == "Kalastuspaikka"
    assert located == "Suomenlinna"


# ---- Review round 7 rerun: fused joints and gradation -------------------------


def test_fused_joint_school_stays_whole():
    # Espoonlahden koulun ja lukion liikuntasali: one joint venue.
    signed = "Espoonlahden koulun ja lukion liikuntasali"
    assert split(make_spider(), signed) == (signed, None, None)


def test_throwing_spot_inverts():
    name, located, official = split(make_spider(), "Pikku Huopalahden ala-asteen koulu / Koripallon heittopaikka")
    assert name == "Koripallon heittopaikka"
    assert located == "Pikku Huopalahden ala-asteen koulu"
    assert official == "Pikku Huopalahden ala-asteen koulu / Koripallon heittopaikka"


def test_genitive_field_shore_normalize():
    spider = make_spider()
    assert cat(spider, "Vasaramäen koulu, Tenniskentän yksikkö")[0] == Categories.LEISURE_PITCH


# ---- Review rounds 8-11: remaining names --------------------------------------


def test_locality_tail_at_health_host_stays_whole():
    # Kalvolan neuvola, Iittala: single-capital tails at non-school
    # institutions are localities, not named units (cf. Sipoon Enter).
    signed = "Kalvolan neuvola, Iittala"
    assert split(make_spider(), signed) == (signed, None, None)


def test_branch_located_dedup_end_to_end():
    spider = make_spider()
    item = parsed(
        spider, channel("Lastentautien poliklinikka, Forssan sairaala", office="FORSSA"), "Kanta-Hämeen hyvinvointialue"
    )
    assert item["name"] == "Lastentautien poliklinikka"
    assert item["located_in"] == "Forssan sairaala"
    assert item.get("branch") is None


def test_rontgen_carries_clinic():
    assert cat(make_spider(), "Katriinan sairaalan röntgen") == (
        Categories.CLINIC,
        {"healthcare": "medical_imaging"},
    )


def test_beach_volley_plural_field():
    category, extra = cat(make_spider(), "Velaatan uimarannan beach volley -kenttä")
    assert category == Categories.LEISURE_PITCH
    assert extra["sport"] == "beachvolleyball"


# ---- Round 12: generic-pool rescue (reviews 12_1..12_6 + user reports) ----


def test_chess_boards_are_pitches():
    spider = make_spider()
    category, extra = cat(spider, "Shakkilauta, Hesperianpuisto")
    assert category == Categories.LEISURE_PITCH
    assert extra == {"sport": "chess"}
    category, extra = cat(spider, "Shakkilaudat, Hakasalmenpuisto")
    assert category == Categories.LEISURE_PITCH
    assert extra == {"sport": "chess"}
    # The activity is not the venue.
    assert cat(spider, "Pelataan yhdessä shakkia") == (None, None)


def test_bay_headed_facilities_split():
    spider = make_spider()
    name, located, official = split(spider, "Töölönlahti / WDC-ulkokuntoilupaikka 1")
    assert name == "WDC-ulkokuntoilupaikka 1"
    assert located == "Töölönlahti"
    assert official == "Töölönlahti / WDC-ulkokuntoilupaikka 1"
    name, located, _ = split(spider, "Tahvonlahti / Hiekkakenttä")
    assert name == "Hiekkakenttä"
    assert located == "Tahvonlahti"
    # The city of Lahti is never a bay head.
    assert split(spider, "Lahti / Matkustajasatama") == ("Lahti / Matkustajasatama", None, None)


def test_playgrounds_at_shores():
    spider = make_spider()
    assert cat(spider, "Leikkipaikka Tokoinranta")[0] == Categories.LEISURE_PLAYGROUND
    assert cat(spider, "Hovirinnan Rantaleikkipuisto")[0] == Categories.LEISURE_PLAYGROUND
    assert cat(spider, "Rantapuiston Leikkikenttä")[0] == Categories.LEISURE_PLAYGROUND
    assert cat(spider, "Pakilan uimaranta")[0] == Categories.NATURAL_BEACH


def test_fishing_spots():
    spider = make_spider()
    assert cat(spider, "Arabianranta / Kalastuspaikka")[1] == {"leisure": "fishing"}
    assert cat(spider, "Eläintarhanlahti ja Tokoinranta / Kalastuspaikka")[1] == {"leisure": "fishing"}
    assert cat(spider, "Tikkurilankosken kalastuslupa-alue")[1] == {"leisure": "fishing"}
    assert cat(spider, "Mykänlammen virkistys ja kalastusalue")[1] == {"leisure": "fishing"}
    # Area shelters keep shelter.
    assert cat(spider, "Niemisjärven kalastusalueen laavu (Evo)")[0] == Categories.SHELTER


def test_courts_and_their_guards():
    spider = make_spider()
    assert cat(spider, "Vakuutusoikeus")[0] == Categories.COURTHOUSE
    assert cat(spider, "Korkein oikeus")[0] == Categories.COURTHOUSE
    assert cat(spider, "Helsingin hallinto-oikeus")[0] == Categories.COURTHOUSE
    assert cat(spider, "Mikkelin Asumisoikeus Oy:n toimisto")[0] == Categories.OFFICE_COMPANY
    assert cat(spider, "Helsingin Asumisoikeus Oy")[0] == Categories.OFFICE_COMPANY
    assert cat(spider, "Oikeuspsykiatrian vastaanotto, Auroran sairaala")[0] == Categories.CLINIC
    assert cat(spider, "Lasten ja nuorten oikeuspsykologian yksikkö")[0] == Categories.CLINIC
    assert cat(spider, "Koulupsykologi")[0] == Categories.CLINIC


def test_civic_boards_are_offices():
    spider = make_spider()
    assert cat(spider, "Helsingin keskusvaalilautakunta")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Helsingin kaupunginvaltuusto")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Hankinnat ja Kilpailuttaminen")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Tonttijako")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Maakuntatalo")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Welcome Office")[0] == Categories.OFFICE_GOVERNMENT
    # Youth councils keep their community filing.
    assert cat(spider, "Nuorisovaltuusto")[0] == Categories.COMMUNITY_CENTRE


def test_group_home_gradation():
    category, extra = cat(make_spider(), "Hakalan ryhmäkodit")
    assert category == Categories.SOCIAL_FACILITY
    assert extra == {"social_facility": "group_home"}


def test_terminals_are_ferry():
    spider = make_spider()
    assert cat(spider, "Hansaterminaali")[0] == Categories.FERRY_TERMINAL
    assert cat(spider, "Länsiterminaali 1")[0] == Categories.FERRY_TERMINAL
    # The food-distribution terminal keeps its social filing.
    assert cat(spider, "Yhteisen pöydän hävikkiterminaali")[0] == Categories.SOCIAL_FACILITY


def test_inpatient_wards_are_clinics():
    assert cat(make_spider(), "Laakson vuodeosasto 13 (infektio-osasto)")[0] == Categories.CLINIC
    assert cat(make_spider(), "Pellon vuodeosasto")[0] == Categories.CLINIC


def test_congress_halls_are_venues():
    assert cat(make_spider(), "Konsertti- ja kongressitalo Mikaeli")[0] == Categories.EVENTS_VENUE


def test_surplus_food_is_social():
    spider = make_spider()
    assert cat(spider, "Hävikkiruoan jako työttömille ja vähävaraisille")[0] == Categories.SOCIAL_FACILITY
    assert cat(spider, "Hävikkiruokajakelu")[0] == Categories.SOCIAL_FACILITY


def test_dump_sites_are_landfill():
    assert cat(make_spider(), "Lumenkaatopaikka")[1] == {"landuse": "landfill"}
    assert cat(make_spider(), "Pielaveden maankaatopaikka")[1] == {"landuse": "landfill"}


def test_contact_channels_drop():
    assert make_spider()._is_dropped_name("Sipoon Veden sähköpostiosoite") == "non_place/contact"
    assert make_spider()._is_dropped_name("Seritatyön sähköpostiosoite") == "non_place/contact"


def test_water_points():
    spider = make_spider()
    assert cat(spider, "Vesipiste veneilijöille")[0] == Categories.DRINKING_WATER
    assert cat(spider, "Pielaveden kunnan yleinen vedenjakelupiste")[0] == Categories.DRINKING_WATER
    assert cat(spider, "Virolahden kunnan vesiposti Virojoella")[0] == Categories.DRINKING_WATER


def test_swedish_housing_is_social():
    item = parsed(make_spider(), channel("Bromarv pensionärsbostäder"))
    assert item.get_tag("amenity") == "social_facility"
    assert item["extras"].get("social_facility:for") == "senior"


def test_register_offices_are_government():
    spider = make_spider()
    assert cat(spider, "Kokkolan aluekeskusrekisteri")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Espoon aluekeskusrekisteri")[0] == Categories.OFFICE_GOVERNMENT


def test_municipal_enterprises_are_company_offices():
    spider = make_spider()
    assert cat(spider, "Kajaanin Vesi -liikelaitos")[0] == Categories.OFFICE_COMPANY
    item = parsed(spider, channel("Kajaanin Vesi -liikelaitos"))
    assert item["name"] == "Kajaanin Vesi -liikelaitos"
    assert item.get_tag("office") == "company"


def test_partnership_houses_are_community():
    spider = make_spider()
    assert cat(spider, "Kumppanuustalo Artteli")[0] == Categories.COMMUNITY_CENTRE
    assert cat(spider, "Järjestötalon aukioloaika")[0] == Categories.COMMUNITY_CENTRE


def test_designated_forests_are_wood():
    assert cat(make_spider(), "Lapinlahden Erikoismetsä")[1] == {"natural": "wood"}


def test_innovation_workshops():
    category, extra = cat(make_spider(), "Innopaja & Kädentaitokeskus")
    assert category == Categories.SOCIAL_FACILITY
    assert extra == {"social_facility": "workshop"}


def test_reuse_points_are_recycling():
    assert cat(make_spider(), "Kiertopisteen materiaali- ja tekstiilipankki")[0] == Categories.RECYCLING


def test_workers_halls_are_community():
    spider = make_spider()
    assert cat(spider, "Vartsalan työväentalo")[0] == Categories.COMMUNITY_CENTRE
    assert cat(spider, "Toimintapäivät Lohjan Työväentalolla")[0] == Categories.COMMUNITY_CENTRE
    # The gym inside still files as a gym.
    assert cat(spider, "Ahtialan työväentalon kuntosali")[0] == Categories.GYM


def test_swedish_dog_parks():
    assert cat(make_spider(), "Hundparken")[0] == Categories.LEISURE_DOG_PARK


def test_cafe_counters_are_cafes():
    assert cat(make_spider(), "Jorvin Terassikahvio")[0] == Categories.CAFE


def test_artwork_titles_stay_generic_for_rescue():
    # Leikkivät karhut (9aa637ca): the title is not a playground;
    # services/ontology rescue it to artwork instead.
    assert cat(make_spider(), "Leikkivät karhut") == (None, None)


def test_bilingual_translations_split():
    item = parsed(
        make_spider(),
        channel(
            "Sodanajan naisen muistomerkki",
            en="Sodanajan naisen muistomerkki / Memorial to Women in Times of War",
            sv="Den krigstida kvinnans minnesmärke",
        ),
    )
    assert item["extras"].get("name:en") == "Memorial to Women in Times of War"
    assert item["extras"].get("name:sv") == "Den krigstida kvinnans minnesmärke"


def test_memorial_slash_names_stay_whole():
    # Moduli / Rakentajaveistos: one artwork under two names, not host+venue.
    item = parsed(
        make_spider(),
        channel(
            "Moduli / Rakentajaveistos",
            en="Moduli (Rakentajaveistos) / The Module",
            sv="Modul / Byggarnas minnesmärke",
        ),
    )
    assert item["name"] == "Moduli / Rakentajaveistos"
    assert item.get("located_in") is None


def test_mid_name_chain_brands_operate():
    # Päiväkoti Pilke Äppelbo: city-purchased but Pilke-operated.
    item = parsed(
        make_spider(),
        channel("Päiväkoti Pilke Äppelbo daghem"),
        "Turun kaupunki, Kasvatuksen ja koulutuksen toimiala",
    )
    assert item["operator"] == "Pilke"
    assert item["extras"].get("operator:type") == "private"


def test_lt_numbers_keep_last():
    item = addressed(make_spider(), "Juurikoskenkatu", "1 lt 7")
    assert item.get("street") == "Juurikoskenkatu"
    assert item.get("housenumber") == "7"


def test_numberless_bare_streets_stay():
    # Raahen rantaraitti / Luolavuoren pulkkamäki rows: bare streets
    # carry the name with no number (review12_1 systemic declined).
    assert addressed(make_spider(), "Ulkofantintie", "").get("street") == "Ulkofantintie"
    assert addressed(make_spider(), "Luolavuorenpolku", "").get("street") == "Luolavuorenpolku"


# ---- Round 13 + code review: ordering, guards, crawl paths ----


def test_specific_halls_outrank_generic():
    spider = make_spider()
    assert cat(spider, "Aleksis Kiven peruskoulu / Juhlasali")[0] == Categories.EVENTS_VENUE
    assert cat(spider, "Stoa / Musiikkisali")[0] == Categories.EVENTS_VENUE
    assert cat(spider, "Mikkelin jäähalli")[0] == Categories.LEISURE_ICE_RINK
    assert cat(spider, "Keilahalli")[0] == Categories.LEISURE_BOWLING_ALLEY
    assert cat(spider, "Tervanapsu autiotupa")[0] == Categories.TOURISM_WILDERNESS_HUT
    assert cat(spider, "Toppelundinrannan koirauimaranta")[0] == Categories.LEISURE_DOG_PARK
    assert cat(spider, "Valtuustosali")[0] == Categories.EVENTS_VENUE


def test_crematoriums():
    spider = make_spider()
    assert cat(spider, "Joensuun krematorio")[1] == {"amenity": "crematorium"}
    assert cat(spider, "Krematorio")[1] == {"amenity": "crematorium"}
    # The parking machine on Krematoriontie stays a machine.
    assert cat(spider, "Pysäköintilippuautomaatti 630, Krematoriontie, korttimaksu")[0] == (Categories.VENDING_MACHINE)


def test_exhibition_venues_are_museums():
    spider = make_spider()
    assert cat(spider, "Näyttelyhalli")[0] == Categories.MUSEUM
    assert cat(spider, "Näyttelykeskus WeeGee")[0] == Categories.MUSEUM
    assert cat(spider, "Leo Torpan kamerakokoelma")[0] == Categories.MUSEUM
    assert cat(spider, "Sonkajärven kirjaston näyttelysali")[0] == Categories.MUSEUM


def test_therapists_are_clinics():
    spider = make_spider()
    category, extra = cat(spider, "Jalkaterapeutti, Loimaa")
    assert category == Categories.CLINIC
    assert extra == {"healthcare": "podiatrist"}
    assert cat(spider, "Varhaiskasvatuksen puheterapeutti")[0] == Categories.CLINIC


def test_support_centres_are_social():
    assert cat(make_spider(), "Perhetukikeskus Päiväperho")[0] == Categories.SOCIAL_FACILITY
    assert cat(make_spider(), "Seri-tukikeskus")[0] == Categories.SOCIAL_FACILITY


def test_waste_plurals_are_recycling():
    assert cat(make_spider(), "Vaarallisten jätteiden autokeräys")[0] == Categories.RECYCLING


def test_kodats_are_shelters():
    assert cat(make_spider(), "Grillikatokset- ja kodat")[0] == Categories.SHELTER


def test_office_desk_pairs_keep_whole():
    spider = make_spider()
    signed = "Pirkanmaan oikeusaputoimisto, Valkeakosken vastaanotto"
    assert split(spider, signed) == (signed, None, None)
    signed = "Tampereen kaupunki, Vastaanotto"
    assert split(spider, signed) == (signed, None, None)


def test_meeting_places_outrank_clientele():
    spider = make_spider()
    assert cat(spider, "Mielenterveyskuntoutujien matalan kynnyksen kohtaamispaikka")[0] == (
        Categories.COMMUNITY_CENTRE
    )
    assert cat(spider, "Nuorten ja nuorten aikuisten kohtaamispaikka JOJO")[0] == Categories.COMMUNITY_CENTRE


def test_court_chancellery_is_courthouse():
    assert cat(make_spider(), "Oulun käräjäoikeus, Ylivieskan kanslia")[0] == Categories.COURTHOUSE


def test_postcode_only_numbers_drop():
    item = addressed(make_spider(), "Kalevalantie 13", "90570")
    assert item.get("street") == "Kalevalantie"
    assert item.get("housenumber") == "13"


def test_pobox_whole_numbers_drop():
    item = addressed(make_spider(), "Tie", "PL 24")
    assert item.get("housenumber") is None


def test_building_space_tails_keep_unit():
    item = addressed(make_spider(), "Tie", "15 rak.1 B-rappu")
    assert item.get("housenumber") == "15"
    assert item["extras"].get("addr:unit") == "rak.1 B-rappu"


def test_lang_value_skips_empty():
    assert PtvFISpider._lang_value([{"language": "fi", "value": ""}, {"language": "fi", "value": "Katu"}], "fi") == (
        "Katu"
    )


def test_sculptures_carry_type():
    category, extra = cat(make_spider(), "Musta graniittiveistos")
    assert category is None
    assert extra == {"tourism": "artwork", "artwork_type": "sculpture"}
    assert cat(make_spider(), "Kauko Kortelaisen veistospuisto")[0] == Categories.LEISURE_PARK


def test_swim_hall_gym_is_gym():
    assert cat(make_spider(), "Itäkeskuksen uimahalli / Liikuntasali")[0] == Categories.GYM


def test_uimahalli_inessive_splits():
    name, located, official = split(make_spider(), "Yhteisökahvila Hollolan uimahallilla")
    assert name == "Yhteisökahvila"
    assert located == "Hollolan uimahalli"
    assert official == "Yhteisökahvila Hollolan uimahallilla"


def test_org_bad_shape_flushes_pending():
    spider = make_spider()
    item = Feature()
    item["name"] = "X"
    spider._pending["org-1"] = [item]

    def _boom():
        raise ValueError("nope")

    bad = SimpleNamespace(url="https://x/?guids=org-1", json=_boom)
    assert list(spider.parse_orgs(bad)) == [item]
    assert spider._pending == {}


def test_pagination_stops_on_repeated_ids():
    from scrapy.http import JsonRequest

    spider = make_spider()
    page = {"itemList": [{"id": "a"}]}
    out1 = list(spider.parse(SimpleNamespace(json=lambda: dict(page)), 1))
    assert any(isinstance(r, JsonRequest) and "page=2" in r.url for r in out1)
    out2 = list(spider.parse(SimpleNamespace(json=lambda: dict(page)), 2))
    assert not any("page=3" in getattr(r, "url", "") for r in out2)


def test_always_open_suppresses_spans():
    spider = make_spider()
    assert (
        spider._hours(
            {
                "serviceHours": [
                    {"serviceHourType": "DaysOfTheWeek", "isAlwaysOpen": True},
                    {
                        "serviceHourType": "DaysOfTheWeek",
                        "openingHour": [{"dayFrom": "Monday", "dayTo": "", "from": "08:00:00", "to": "16:00:00"}],
                    },
                ]
            }
        )
        == "24/7"
    )


def test_dangling_preposition_city_kept():
    # International School of Helsinki: stripping the city strands "of".
    signed = "Päiväkoti International School of Helsinki"
    assert split(make_spider(), signed, "Helsinki") == (signed, None, None)


def test_artwork_titles():
    assert cat(make_spider(), 'Taideteos "Turvapaikka" osa 1')[0] == Categories.TOURISM_ARTWORK


def test_district_tails_drop():
    item = addressed(make_spider(), "Tivolikuja", "1 Alppiharju")
    assert item.get("street") == "Tivolikuja"
    assert item.get("housenumber") == "1"


def test_shelters_outrank_stations():
    # Sörnäisten metroaseman yleinen väestönsuoja: the shelter names the
    # POI, the inflected station modifier must not file it as a station.
    category, extra = cat(make_spider(), "Sörnäisten metroaseman yleinen väestönsuoja")
    assert category == Categories.MILITARY_BUNKER
    assert extra == {"bunker_type": "bomb_shelter"}
    assert cat(make_spider(), "Kampin metroaseman yleinen väestönsuoja")[0] == Categories.MILITARY_BUNKER


def test_station_compounds_file_as_facilities():
    spider = make_spider()
    assert cat(spider, "Vesilahden lähiasema")[0] == Categories.CLINIC
    assert cat(spider, "Selviämishoitoasema")[0] == Categories.CLINIC
    assert cat(spider, "Selviämisasema")[0] == Categories.CLINIC
    assert cat(spider, "Sydänasema")[0] == Categories.CLINIC
    assert cat(spider, "Krossin pelastus- ja ensihoitoasema")[0] == Categories.FIRE_STATION
    assert cat(spider, "Tervolan Ekoasema")[0] == Categories.RECYCLING
    assert cat(spider, "ViaDian Kohtaamisasema")[0] == Categories.COMMUNITY_CENTRE
    assert cat(spider, "Miesten asema")[0] == Categories.COMMUNITY_CENTRE
    assert cat(spider, "BusinessAsema")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Purasjoen puolustusasema 1939")[0] == Categories.TOURISM_ATTRACTION
    assert cat(spider, "Asemakaavoitus")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Testausasema") == (None, None)


def test_station_needs_word_boundary():
    spider = make_spider()
    assert cat(spider, "Kampin metroasema")[1] == {"railway": "station", "public_transport": "station"}
    assert cat(spider, "Leinelän asema")[1] == {"railway": "station", "public_transport": "station"}
    # Inflected station modifiers without facility words stay generic.
    assert cat(spider, "Asematien Pysäkki") == (None, None)
    # Health-station names in inflected form still type health, not stations.
    assert cat(spider, "Neuvonta terveysasemalla")[0] == Categories.CLINIC


def test_schoolyard_exercise_grounds():
    # Service-map activity refinement: ball arenas are pitches, schoolyards
    # read as playgrounds, other grounds stay fitness stations.
    spider = make_spider()
    assert cat(spider, "Åshöjdens grundskola / Lähiliikuntapaikka")[0] == Categories.LEISURE_PLAYGROUND
    assert cat(spider, "Porolahden peruskoulu / Lähiliikuntapaikka")[0] == Categories.LEISURE_PLAYGROUND
    assert cat(spider, "Landbonkenttä / Lähiliikuntapaikka (Miniareena)")[0] == Categories.LEISURE_PITCH
    assert cat(spider, "Lähiliikuntapaikka")[0] == Categories.LEISURE_FITNESS_STATION


def test_botanical_gardens():
    # Talvipuutarha (Nähtävyydet service, botanical onto): garden, never the
    # farm service's social facility.
    garden = {"leisure": "botanical_garden"}
    assert cat(make_spider(), "Talvipuutarha") == (None, garden)
    assert cat(make_spider(), "Kasvitieteellinen puutarha") == (None, garden)
    assert cat(make_spider(), "Koivuhaan arboretum") == (None, garden)


def test_event_areas_are_not_parks():
    assert cat(make_spider(), "Pengerpuisto, tapahtuma-alue")[0] == Categories.EVENTS_VENUE


def test_institution_hosted_exercise_grounds_name_the_ground():
    # Vuoniityn peruskoulu / Lähiliikuntapaikka: the ground names the POI,
    # the school the venue (cf. slash_room). Non-school heads keep head-first.
    spider = make_spider()
    signed = "Vuoniityn peruskoulu / Lähiliikuntapaikka"
    assert named(spider, signed) == ("Lähiliikuntapaikka", "Vuoniityn peruskoulu", signed)
    signed = "Myllypuron peruskoulu / Lähiliikuntapaikka 2"
    assert named(spider, signed) == ("Lähiliikuntapaikka 2", "Myllypuron peruskoulu", signed)
    signed = "Leikkipuisto Lampi / Lähiliikuntapaikka"
    assert named(spider, signed) == ("Leikkipuisto Lampi", "Lähiliikuntapaikka", signed)


def test_info_and_exercise_points_outrank_hosts():
    spider = make_spider()
    assert cat(spider, "Talin liikuntapuisto / Opastuspiste")[0] == Categories.TOURISM_INFORMATION
    assert cat(spider, "Vanhan-Mankkaan puiston kuntoilupiste 1")[0] == Categories.LEISURE_FITNESS_STATION


def test_fi_duplicates_strip_from_translations():
    # Korsverk (Ristikko): the parenthesised fi name drops, the translation stays.
    item = parsed(make_spider(), channel("Ristikko", sv="Korsverk (Ristikko)", en="Crosses"))
    assert item["extras"].get("name:sv") == "Korsverk"
    assert item["extras"].get("name:en") == "Crosses"


def test_truncated_fi_segment_splits_from_translation():
    # Filosofia, lääketiede.../ Philosophy...: the truncated fi segment drops.
    item = parsed(
        make_spider(),
        channel(
            "Filosofia, Lääketiede, Teologia ja Juridiikka",
            en="Filosofia, lääketiede.../ Philosophy, Medicine, Theology and Justice",
        ),
    )
    assert item["extras"].get("name:en") == "Philosophy, Medicine, Theology and Justice"


def test_venue_prefix_strips_from_translation():
    # Aninkaisten koulu (Aninkainen School) Gym A: the Finnish venue prefix
    # duplicates located_in; the translated rest stays verbatim (feed parens kept).
    item = parsed(make_spider(), channel("Aninkaisten koulun A-sali", en="Aninkaisten koulu (Aninkainen School) Gym A"))
    assert item.get("located_in") == "Aninkaisten koulu"
    assert item["extras"].get("name:en") == "(Aninkainen School) Gym A"


def test_untranslated_venue_copy_is_no_translation():
    # Leikkipuisto Jakomäki as en duplicates the Finnish-signed venue: dropped.
    item = parsed(make_spider(), channel("Leikkipuisto Jakomäki / Hiekkakenttä", en="Leikkipuisto Jakomäki"))
    assert item.get("located_in") == "Leikkipuisto Jakomäki"
    assert "name:en" not in (item.get("extras") or {})


def test_hospital_wards_venue_the_hospital():  # Raskauden seurantaosasto, Tyks Majakkasairaala: the ward names the POI
    # (cf. yksikkö units splitting the same way).
    spider = make_spider()
    signed = "Raskauden seurantaosasto, Tyks Majakkasairaala, Turku"
    assert split(spider, signed, "Turku") == (
        "Raskauden seurantaosasto",
        "Tyks Majakkasairaala",
        signed,
    )
    signed = "Lasten ja nuorten osasto, Ahveniston sairaala"
    assert split(spider, signed) == ("Lasten ja nuorten osasto", "Ahveniston sairaala", signed)


def test_city_switchboards_drop():
    # Vantaan vaihde 09 839 11 serves 145 city rows: never a direct contact.
    spider = make_spider()
    item = Feature()
    spider._apply_contact(item, {"phoneNumbers": [{"prefixNumber": "+358", "number": "983911"}]})
    assert item.get("phone") is None


def test_sininauha_is_private():
    # Satakunnan Sininauha ry (0225013-4): Blue-Ribbon association, no PTV marker.
    assert make_spider()._is_private_org("Satakunnan Sininauha") is True


def test_tourist_info_names_beat_office_hosts():
    # Matkailuneuvonta/matkailuinfo are tourist info desks, not generic
    # offices — even inside toimipiste/palvelupiste hosts. The luontotupa
    # dual keeps the hut (tupa rule stays earlier).
    spider = make_spider()
    assert cat(spider, "Matkailuneuvontapiste Sulkavalla")[0] == Categories.TOURISM_INFORMATION
    assert cat(spider, "Laitilan matkailuinfopiste")[0] == Categories.TOURISM_INFORMATION
    assert cat(spider, "Visit Pori Matkailuneuvonta")[0] == Categories.TOURISM_INFORMATION
    assert cat(spider, "Matkailuinfon toimipiste")[0] == Categories.TOURISM_INFORMATION
    assert cat(spider, "Matkailuneuvonnan palvelupiste")[0] == Categories.TOURISM_INFORMATION
    assert cat(spider, "Koloveden luontotupa ja matkailuneuvonta")[0] == Categories.COMMUNITY_CENTRE


def test_hosted_desks_file_as_desks():
    # Sote-aseman lähitori names the desk (74 sibling lähitori rows file
    # social_facility); plain youth stations stay offices, but the
    # mental-health Nuorisoasema is a clinic.
    spider = make_spider()
    assert cat(spider, "Pirkkalan sote-aseman lähitori")[0] == Categories.SOCIAL_FACILITY
    assert cat(spider, "Nuorisoasema mielenterveystyö")[0] == Categories.CLINIC
    assert cat(spider, "Nuorisoasema Klaara")[0] == Categories.OFFICE_GOVERNMENT


def test_single_digit_country_typo_repairs():
    # "+359 447301262" on an Ikaalinen row: Bulgarian code on a Finnish
    # mobile shape, one digit off every other row — repair, don't pass on.
    assert make_spider()._normalize_phone("+359 447301262") == "+358 44 7301262"


def test_supported_housing_beats_diagnosis():
    # Etu-Töölön asuintalo filed clinic via mental-health rescue; the POI
    # is supported housing (Mielenterveyskuntoutujien tuettu asuminen).
    spider = make_spider()
    assert cat(spider, "Mielenterveyskuntoutujien tuettu asuminen")[0] == Categories.ASSISTED_LIVING
    ch = channel("Etu-Töölön asuintalo")
    ch["services"] = [{"service": {"name": "Mielenterveyskuntoutujien tuettu asuminen"}}]
    item = parsed(spider, ch)
    assert item.get_tag("amenity") == "social_facility"
    assert item["extras"].get("social_facility") == "assisted_living"


def test_utility_buildings_stay_generic():
    # "... / Huoltorakennus" with Urheilukentät services: the building
    # names the POI, not its services — rescue leaves it generic.
    spider = make_spider()
    ch = channel("Eläintarhan urheilukenttä / Huoltorakennus 3")
    ch["services"] = [{"service": {"name": "Urheilukentät"}}]
    item = parsed(spider, ch)
    assert item.get_tag("amenity") == "yes"
    assert item.get_tag("leisure") is None


def test_room_tails_type_the_poi():
    # Facility tails name the POI ("Hietarannan uimaranta /
    # Koripallokenttä"): the tail types it, not the beach host.
    spider = make_spider()
    assert cat(spider, "Hietarannan uimaranta / Koripallokenttä")[0] == Categories.LEISURE_PITCH
    assert named(spider, "Hietarannan uimaranta / Koripallokenttä") == (
        "Koripallokenttä",
        "Hietarannan uimaranta",
        "Hietarannan uimaranta / Koripallokenttä",
    )
    assert named(spider, "Väinämöisenkenttä / Ulkokuntoilupaikka") == (
        "Ulkokuntoilupaikka",
        "Väinämöisenkenttä",
        "Väinämöisenkenttä / Ulkokuntoilupaikka",
    )
    assert cat(spider, "Hietarannan uimaranta / Ulkokuntoilupaikka (Keski)")[0] == (Categories.LEISURE_FITNESS_STATION)


def test_compound_and_typeless_tails_keep_full_filing():
    # "Sipoon opisto / Opintien palvelupiste ja liikuntatila" stays a
    # college; "Maunulan liikuntahalli / Sisäampumarata" stays a hall;
    # institution tails hosting activities keep full-form filing.
    spider = make_spider()
    assert cat(spider, "Sipoon opisto / Opintien palvelupiste ja liikuntatila")[0] == Categories.COLLEGE
    assert cat(spider, "Maunulan liikuntahalli / Sisäampumarata")[0] == Categories.LEISURE_SPORTS_CENTRE
    assert cat(spider, "Iltapäivätoiminta / Puotilan ala-aste, Saalem-Nuoret ry")[0] == Categories.COMMUNITY_CENTRE


def test_parenthesised_room_tails_split():
    # "Hietarannan uimaranta / Ulkokuntoilupaikka (Keski)": the tailed
    # facility names the POI, parens included, the beach hosts it.
    spider = make_spider()
    assert named(spider, "Hietarannan uimaranta / Ulkokuntoilupaikka (Keski)") == (
        "Ulkokuntoilupaikka (Keski)",
        "Hietarannan uimaranta",
        "Hietarannan uimaranta / Ulkokuntoilupaikka (Keski)",
    )
    assert named(spider, "Malmitalo / Esiintymisali (Pieni sali)") == (
        "Esiintymisali (Pieni sali)",
        "Malmitalo",
        "Malmitalo / Esiintymisali (Pieni sali)",
    )


def test_grill_places_are_picnic_sites():
    # "Seurasaari / Grillipaikka" filed park via park-service rescue; a
    # grill place is a picnic site. kota/katos shelters keep shelter.
    spider = make_spider()
    assert cat(spider, "Seurasaari / Grillipaikka")[0] == Categories.TOURISM_PICNIC_SITE
    assert cat(spider, "Meri-Rastila / Grillipaikka")[0] == Categories.TOURISM_PICNIC_SITE
    assert cat(spider, "Malmin kenttä / Väliaikainen grillipaikka")[0] == Categories.TOURISM_PICNIC_SITE


def test_orienteering_controls_stay_generic():
    # Otaniemen kiintorastit filed shooting_ground via ampumaradat
    # ontology dumps; fixed controls are markers, not ranges.
    spider = make_spider()
    ch = channel("Otaniemen kiintorastit")
    ch["services"] = [{"service": {"name": "Liikunnan ja urheilun tulosyksikkö"}}]
    ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": "ampumaradat"}]}]
    item = parsed(spider, ch)
    assert item.get_tag("amenity") == "yes"
    assert item.get_tag("leisure") is None


def test_outdoor_islands_are_islands():
    # "Porsas" filed social_facility via a petting-farm service; with
    # Ulkoilusaaret services it is an island like its siblings.
    spider = make_spider()
    ch = channel("Porsas")
    ch["services"] = [
        {"service": {"name": "Haltialan kotieläintila"}},
        {"service": {"name": "Ulkoilusaaret"}},
    ]
    item = parsed(spider, ch)
    assert item["extras"].get("place") == "island"


def test_home_care_beats_local_service_areas():
    # "Kotihoito/Töölö 2 lähipalvelualue" filed office via lähipalvelu;
    # home care outranks the coverage-area tail. Genitive näytteenoton
    # sampling points file as sampling, not offices.
    spider = make_spider()
    assert cat(spider, "Kotihoito/Töölö 2 lähipalvelualue")[0] == Categories.SOCIAL_FACILITY
    assert cat(spider, "Kotihoito/Pitäjänmäki 1 lähipalvelualue")[0] == Categories.SOCIAL_FACILITY
    assert cat(spider, "Oulun Limingantulli-Meritulli kotihoito")[0] == Categories.SOCIAL_FACILITY
    assert cat(spider, "Veikkolan näytteenoton lähipalvelu")[0] == Categories.SAMPLE_COLLECTION


def test_forskola_is_kindergarten():
    # "Kyrkoby förskola" filed school via the skola regex; förskola is
    # a Swedish preschool like daghem/dagis.
    spider = make_spider()
    assert cat(spider, "Kyrkoby förskola")[0] == Categories.KINDERGARTEN
    assert cat(spider, "Söderkulla förskola")[0] == Categories.KINDERGARTEN


def test_care_homes_beat_care_desks():
    # "Hoitokoti Toppila" filed office via the bare hoito desk rule;
    # care homes are nursing homes. Family daycare homes keep theirs.
    spider = make_spider()
    assert cat(spider, "Hoitokoti Toppila")[0] == Categories.NURSING_HOME
    assert cat(spider, "Hoitokoti, Hyrynsalmen hoitokoti")[0] == Categories.NURSING_HOME
    assert cat(spider, "Eläinhoitola")[0] == Categories.VETERINARY
    assert cat(spider, "Heinolan Lintuhoitola")[0] == Categories.VETERINARY
    assert cat(spider, "Ryhmäperhepäivähoitokoti Rastas")[0] == Categories.KINDERGARTEN


def test_training_courses_are_not_schools():
    # "Koulutukset ja luennot" filed school via the koulu lookahead gap
    # (koulutuksen/tukset continue with tuk, not tus); courses are desks.
    spider = make_spider()
    assert cat(spider, "Koulutukset ja luennot")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Kasvatuksen ja koulutuksen toimiala, hallinto")[0] == Categories.OFFICE_GOVERNMENT


def test_school_compounds_keep_facility():
    # "Koulumuseo" and "Koulutoimisto" filed school; the facility word
    # is the second compound element (museum, education office).
    spider = make_spider()
    assert cat(spider, "Koulumuseo Lagstad")[0] == Categories.MUSEUM
    assert cat(spider, "Saukkojärven kotiseutu- ja koulumuseo")[0] == Categories.MUSEUM
    assert cat(spider, "Vesilahden koulutoimisto")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Koulutoimisto")[0] == Categories.OFFICE_GOVERNMENT


def test_tupa_yields_to_care_venues():
    # The compound-end tupa rule shadowed later care/office/park rules:
    # care homes, day centres, shores, desks and culture houses file as
    # themselves now. The luontotupa dual keeps the hut (pinned).
    spider = make_spider()
    assert cat(spider, "Iin palvelukoti Emmintupa")[0] == Categories.NURSING_HOME
    assert cat(spider, "Palvelukoti Snällintupa")[0] == Categories.NURSING_HOME
    assert cat(spider, "Rovaniemen päiväkeskus Veitikantupa")[0] == Categories.SOCIAL_FACILITY
    assert cat(spider, "Salmen ulkoilualue / Taukotupa")[0] == Categories.LEISURE_PARK
    assert cat(spider, "Asiakaspalvelupiste Tietotupa")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Lastenkulttuurikeskus Pyykkitupa")[0] == Categories.ARTS_CENTRE
    assert cat(spider, "Koloveden luontotupa ja matkailuneuvonta")[0] == Categories.COMMUNITY_CENTRE


def test_library_reading_rooms_are_libraries():
    # "Valkeakosken kaupunginkirjaston lehtisali" filed sports hall via
    # sali; the head is the library, the tail a reading room.
    spider = make_spider()
    assert cat(spider, "Valkeakosken kaupunginkirjaston lehtisali")[0] == Categories.LIBRARY
    assert cat(spider, "Lehtilukusali")[0] == Categories.LIBRARY
    assert cat(spider, "Lehtisali ja omatoimikirjasto")[0] == Categories.LIBRARY


def test_housing_plural_stems():
    # One unlisted spelling per venue family went untyped: supported
    # flats, service flats (filed office via palvelu), joint shelters,
    # parish centres/premises and short-stay units.
    spider = make_spider()
    assert cat(spider, "Roihuvuoren tukiasunnot")[0] == Categories.ASSISTED_LIVING
    assert cat(spider, "Ruusukujan palveluasunnot")[0] == Categories.NURSING_HOME
    assert cat(spider, "Lehtisaaren yhteiskalliosuoja")[0] == Categories.MILITARY_BUNKER
    assert cat(spider, "Linnainmaan seurakuntakeskus")[0] == Categories.COMMUNITY_CENTRE
    assert cat(spider, "Seurakuntatila Kauksun Kulma")[0] == Categories.COMMUNITY_CENTRE
    assert cat(spider, "Lyhytaikaisyksikkö Selvari, Seinäjoki")[0] == Categories.NURSING_HOME


def test_customs_rule_skips_place_names():
    # "Tullinkulma"/"Tullikamari"/crosswalk filed customs office via the
    # bare tulli substring; only genuine customs (Lentotulli) keeps it.
    spider = make_spider()
    assert cat(spider, "Lentotulli")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Tullinkulma")[0] is None
    assert cat(spider, "Tullikamari")[0] is None
    assert cat(spider, "Myllytullin koulu")[0] == Categories.SCHOOL


def test_service_info_compounds_keep_service():
    # "Seniori-info" and "Kansalaisinfo" filed tourist info; senior and
    # citizen desks file as themselves. Bone-health info is an association desk, not a clinic.
    spider = make_spider()
    assert cat(spider, "Seniori-info")[0] == Categories.SOCIAL_FACILITY
    assert cat(spider, "Yhteispalvelu Vaasa - Kansalaisinfo")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Luustoinfo osteoporoosia sairastaville / Lahti")[0] == Categories.OFFICE_GOVERNMENT


def test_square_guard_keeps_venues():
    # Facility venues at squares filed place=square with no category:
    # daycares, care homes, pharmacies, coordinators and schools file as
    # themselves; bare squares stay squares.
    spider = make_spider()
    assert cat(spider, "Päiväkoti Vihtori")[0] == Categories.KINDERGARTEN
    assert cat(spider, "Esperi Hoivakoti Vihtori")[0] == Categories.NURSING_HOME
    assert cat(spider, "Kotkan 5. Karhulan Tori apteekki")[0] == Categories.PHARMACY
    assert cat(spider, "Hämeenlinnan I Tori-apteekki")[0] == Categories.PHARMACY
    assert cat(spider, "Terveyskeskus Mehiläinen Espoontori")[0] == Categories.CLINIC
    assert cat(spider, "Tiernan koulu, Heinätori")[0] == Categories.SCHOOL
    assert cat(spider, "Työllisyyskoordinaattori")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Kiuruveden tori")[0] is None
    assert cat(spider, "Kuusijärven saunat")[0] == Categories.SAUNA


def test_island_titled_artworks_are_art():
    # "Saari" with Julkinen taide services (HAM) is public art, not land.
    spider = make_spider()
    ch = channel("Saari")
    ch["services"] = [{"service": {"name": "Julkinen taide"}}]
    ch["ontologyTerms"] = [
        {"name": [{"language": "fi", "value": "julkinen taide"}]},
        {"name": [{"language": "fi", "value": "veistokset"}]},
    ]
    item = parsed(spider, ch)
    assert item["extras"].get("tourism") == "artwork"


def test_stray_space_before_comma_collapses():
    # "Prästgårdsbackens förskola , Gesterby" carries feed dirt; the
    # comma still parses the same (village kept, kindergarten kept).
    spider = make_spider()
    assert spider._clean_name("Prästgårdsbackens förskola , Gesterby") == ("Prästgårdsbackens förskola, Gesterby")
    assert cat(spider, "Prästgårdsbackens förskola, Gesterby")[0] == Categories.KINDERGARTEN


def test_bone_info_is_an_association_desk():
    # "Luustoinfo osteoporoosia sairastaville / Lahti" is a patient-association
    # info desk (Suomen Luustoliitto ry), not a clinic; the operator tier
    # demotes association desks to office=association.
    spider = make_spider()
    assert cat(spider, "Luustoinfo osteoporoosia sairastaville / Lahti")[0] == Categories.OFFICE_GOVERNMENT
    ch = channel("Luustoinfo osteoporoosia sairastaville / Lahti")
    item = parsed(spider, ch, org_name="Suomen Luustoliitto ry")
    assert item["extras"].get("office") == "association"


def test_shelters_carry_shelter_subtype():
    # "Mikkelin turvakoti" is a domestic-violence shelter; desks keep
    # filing as offices.
    spider = make_spider()
    assert cat(spider, "Mikkelin turvakoti") == (
        Categories.SOCIAL_FACILITY,
        {"social_facility": "shelter"},
    )
    assert cat(spider, "Turvakoti palvelupiste")[0] == Categories.OFFICE_GOVERNMENT


def test_branch_duplicating_name_drops():
    # "Korva-, nenä- ja kurkkutautien poliklinikka" branched to itself;
    # the name keeps the full form, branch goes null.
    spider = make_spider()
    item = parsed(spider, channel("Korva-, nenä- ja kurkkutautien poliklinikka"))
    assert item.get("branch") is None
    assert item["name"] == "Korva-, nenä- ja kurkkutautien poliklinikka"


def test_elderly_day_activity_is_social():
    # "Ikäihmisten päivätoiminta, Kihniö" is day activity, not residential
    # nursing, even with an elderly clientele.
    spider = make_spider()
    assert cat(spider, "Ikäihmisten päivätoiminta, Kihniö")[0] == Categories.SOCIAL_FACILITY


def test_school_hosted_health_names_service():
    # "Merilahden peruskoulu, Jaluspolun toimipiste, kouluterveydenhuolto":
    # the service names the POI per service@school, the school hosts it.
    spider = make_spider()
    assert named(spider, "Merilahden peruskoulu, Jaluspolun toimipiste, kouluterveydenhuolto") == (
        "Kouluterveydenhuolto",
        "Merilahden peruskoulu, Jaluspolun toimipiste",
        "Merilahden peruskoulu, Jaluspolun toimipiste, kouluterveydenhuolto",
    )
    assert cat(spider, "Merilahden peruskoulu, Jaluspolun toimipiste, kouluterveydenhuolto")[0] == Categories.CLINIC


def test_road_city_tail_parses():
    # "Pappilantie 11, pielavesi" with an empty number field: the city tail
    # repeats the structured city, the head parses as street + number.
    spider = make_spider()
    item = addressed(spider, "Pappilantie 11, pielavesi", "", office="PIELAVESI")
    assert item["street"] == "Pappilantie"
    assert item["housenumber"] == "11"


def test_city_in_number_field_drops():
    # "Tahtimarssi 3" with number "Oulu": the city leaked into the number
    # field, the road parses alone.
    spider = make_spider()
    item = addressed(spider, "Tahtimarssi 3", "Oulu", office="OULU")
    assert item["street"] == "Tahtimarssi"
    assert item["housenumber"] == "3"


def test_swim_lessons_stay_generic():
    # "Uimakoulut" and rescue candidates name lessons, not school buildings;
    # "Hakolan hiekkamonttu" with beach ontology files as a beach.
    spider = make_spider()
    assert cat(spider, "Uimakoulut")[0] is None
    ch = channel("Hakolan hiekkamonttu")
    ch["services"] = [{"service": {"name": "Vesiliikunta"}}]
    ch["ontologyTerms"] = [
        {"name": [{"language": "fi", "value": v}]} for v in ("uimakoulut", "uimarannat", "uimavesi", "uinti")
    ]
    assert parsed(spider, ch)["extras"].get("natural") == "beach"


def test_observation_towers_are_viewpoints():
    # "Vaarniemen näköalatorni" filed allotments via cultivation ontology;
    # the name keyword types it like its lintutorni siblings.
    spider = make_spider()
    assert cat(spider, "Vaarniemen näköalatorni") == (
        Categories.TOURISM_VIEWPOINT,
        {"man_made": "tower", "tower:type": "observation"},
    )


def test_ice_holes_are_swimming_areas():
    # "Haaruksen Jämä-majan avanto" is an ice-swimming hole; pharmacy
    # compounds containing "avanto" keep filing as pharmacies.
    spider = make_spider()
    assert cat(spider, "Haaruksen Jämä-majan avanto")[0] == Categories.LEISURE_SWIMMING_AREA
    assert cat(spider, "Kirjavantolpan apteekki")[0] == Categories.PHARMACY


def test_society_operators_are_private():
    # "Hollolan Nuorisoseura" and kerho societies are associations, never
    # public; parishes stay public-law bodies.
    spider = make_spider()
    assert spider._is_private_org("Hollolan Nuorisoseura") is True
    assert spider._is_private_org("Joensuun bridgekerho ry") is True
    assert spider._is_private_org("Tampereen seurakunnat") is False
    ch = channel("Kansantanssin aikuisten ryhmä Vilhot ja Vienot - Hollola")
    item = parsed(spider, ch, org_name="Hollolan Nuorisoseura")
    assert item["extras"].get("operator:type") == "private"


def test_inessive_compound_hosts_split():
    # "Lohjan Sydän digiopastusta Lohjan pääkirjastossa": compound hosts
    # de-inflect and genitive-mixed heads split; plain rows keep working.
    spider = make_spider()
    assert named(spider, "Lohjan Sydän digiopastusta Lohjan pääkirjastossa") == (
        "Lohjan Sydän digiopastusta",
        "Lohjan pääkirjasto",
        "Lohjan Sydän digiopastusta Lohjan pääkirjastossa",
    )
    assert named(spider, "Martat neuvoo Haminan kirjastossa") == (
        "Martat neuvoo",
        "Haminan kirjasto",
        "Martat neuvoo Haminan kirjastossa",
    )


def test_leisure_house_hosts_locate():
    # "Naisten kuntosaliryhmä, Kaukajärven vapaa-aika talo": the service
    # head names the POI, the leisure house hosts it.
    spider = make_spider()
    assert named(spider, "Naisten kuntosaliryhmä, Kaukajärven vapaa-aika talo") == (
        "Naisten kuntosaliryhmä",
        "Kaukajärven vapaa-aika talo",
        "Naisten kuntosaliryhmä, Kaukajärven vapaa-aika talo",
    )


def test_slash_registry_tails_clean():
    # "Ite ja yhessä - toiminta/Kyläryhmä -palvelun järjestämispaikka,
    # Virolahti 2": registry text drops from located_in, the sub-unit stays.
    spider = make_spider()
    item = parsed(
        spider,
        channel("Ite ja yhessä - toiminta/Kyläryhmä -palvelun järjestämispaikka, Virolahti 2"),
    )
    assert item["located_in"] == "Kyläryhmä"


def test_dash_city_tail_drops():
    # "Kansantanssin aikuisten ryhmä Vilhot ja Vienot - Hollola" repeats
    # the municipality after a dash; the tail drops, official keeps full.
    spider = make_spider()
    ch = channel(
        "Kansantanssin aikuisten ryhmä Vilhot ja Vienot - Hollola -palvelun järjestämispaikka",
        road="Katu",
        street_number="1",
        office="HOLLOLA",
    )
    item = parsed(spider, ch)
    assert item["name"] == "Kansantanssin aikuisten ryhmä Vilhot ja Vienot"


def test_comma_city_lead_peels():
    # "Avustajakurssi, Pori - vapaaehtoistoimintaan mukaan!": the city lead
    # peels off the comma tail, the tagline drops as a descriptor.
    spider = make_spider()
    assert named(spider, "Avustajakurssi, Pori - vapaaehtoistoimintaan mukaan!", city="Pori") == (
        "Avustajakurssi",
        None,
        "Avustajakurssi, Pori - vapaaehtoistoimintaan mukaan!",
    )


def test_contact_placeholder_names_fall_back():
    # A channel named only "Kontaktuppgifter" (contact details) falls back
    # to its real alternative name instead of emitting the placeholder.
    spider = make_spider()
    names = spider._names(
        {
            "serviceChannelNames": [
                {"language": "sv", "value": "Kontaktuppgifter", "type": "Name"},
                {"language": "sv", "value": "AMS", "type": "AlternativeName"},
            ]
        }
    )
    assert names.get("sv") == "AMS"


def test_bare_slash_twins_keep_both_sides():
    # "Lauttasaaren silta/ Kaapelitehdas" (bare slash, no spaces) keeps
    # both translation sides; only spaced-slash twins follow the split.
    spider = make_spider()
    item = parsed(
        spider,
        channel("Lauttasaaren silta/ Kaapelitehdas", sv="Drumsö bro/ Kabelfabriken"),
    )
    assert item["extras"].get("name:sv") == "Drumsö bro/ Kabelfabriken"


def test_dangling_shown_skips_positional_strip():
    # A mis-split shown ending in a comma fragment ("..., Helsingin")
    # must not drive translation stripping; the full form stays.
    spider = make_spider()
    assert (
        spider._split_bilingual(
            "After-school activities / University of Helsinki",
            "Viikin normaalikoulun iltapäivätoiminta, Helsingin",
            "Iltapäivätoiminta / Viikin normaalikoulun iltapäivätoiminta, Helsingin yliopisto",
            "Iltapäivätoiminta",
        )
        == "After-school activities / University of Helsinki"
    )


def test_bird_platforms_are_viewpoints():
    # "Viikki-Vanhankaupunginlahti, Lammassaaren esteetön lintulava" filed
    # park; a bird platform is a viewpoint like its lintutorni siblings.
    spider = make_spider()
    assert cat(spider, "Viikki-Vanhankaupunginlahti, Lammassaaren esteetön lintulava")[0] == (
        Categories.TOURISM_VIEWPOINT
    )


def test_grill_tails_name_the_poi():
    # "Stoan aukio / Grillipaikka" kept the square as the name; the grill
    # facility names the POI wherever it sits, like beach and island hosts.
    spider = make_spider()
    assert named(spider, "Stoan aukio / Grillipaikka") == (
        "Grillipaikka",
        "Stoan aukio",
        "Stoan aukio / Grillipaikka",
    )
    assert named(spider, "Tullisaari / Grillipaikka") == (
        "Grillipaikka",
        "Tullisaari",
        "Tullisaari / Grillipaikka",
    )


def test_located_duplicates_drop_from_translations():
    # Trailing located_in copies ride along in feed translations
    # ("Daghemskök, Päiväkoti Jollas"); the applied name's rendering stays.
    spider = make_spider()
    ch = channel(
        "Päiväkotikeittiö, Päiväkoti Jollas",
        sv="Daghemskök, Päiväkoti Jollas",
        en="Daycare centre kitchen, Daycare Jollas",
    )
    item = parsed(spider, ch)
    assert item["extras"].get("name:sv") == "Daghemskök"
    assert item["extras"].get("name:en") == "Daycare centre kitchen"


def test_slash_twins_follow_the_split():
    # "Oskarinpuisto / Lentopallokenttä" names the field; the Swedish twin
    # of the park side drops, the field's rendering stays. Venue-only
    # remainders ("Utfärdsholme" for located Ulkoilusaari) drop entirely.
    spider = make_spider()
    item = parsed(spider, channel("Oskarinpuisto / Lentopallokenttä", sv="Oskariparken / Volleybollplan"))
    assert item["extras"].get("name:sv") == "Volleybollplan"
    item = parsed(
        spider,
        channel("Bylandet / Ulkoilusaari", sv="Bylandet / Utfärdsholme", en="Bylandet / Recreational island"),
    )
    assert item["extras"].get("name:sv") is None
    assert item["extras"].get("name:en") is None
    assert item.get("located_in") is None
