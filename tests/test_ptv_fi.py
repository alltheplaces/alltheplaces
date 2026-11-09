# -*- coding: utf-8 -*-
"""Behavioural tests for ptv_fi.

Table-driven: each section pins one pipeline stage with parametrised rows
(feed string in, filing out). Bespoke multi-step flows (org joins, errbacks,
stats counters, rescue chains) stay as plain functions. User-report batches
(R-A..R-D) keep their rows verbatim as the report trail; a few of those
inputs also appear in the thematic tables as the systematic index.

Helpers: split()/named() isolate _split_name (raw vs cleaned input);
cat() isolates _category; addressed() isolates _apply_address;
parsed()/channel() run the full parse_channel path.
"""

import json
from types import SimpleNamespace

import pytest
from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
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


# ---- Table drivers -----------------------------------------------------------
# _SKIP: don't assert this field. PRESENT: assert is not None.

_SKIP = object()
PRESENT = object()


def check_cat(fi, want_cat=_SKIP, want_extra=_SKIP):
    assert want_cat is not _SKIP or want_extra is not _SKIP, "check_cat pins nothing"
    got_cat, got_extra = make_spider()._category(fi)
    if want_cat is not _SKIP:
        assert got_cat == want_cat, fi
    if want_extra is not _SKIP:
        assert got_extra == want_extra, fi


def check_split(fi, city, name, located, official, via="split"):
    spider = make_spider()
    got = split(spider, fi, city) if via == "split" else named(spider, fi, city)
    for got_v, want_v, field in (
        (got[0], name, "name"),
        (got[1], located, "located"),
        (got[2], official, "official"),
    ):
        if want_v is _SKIP:
            continue
        if want_v is PRESENT:
            assert got_v is not None, (fi, field, got)
        else:
            assert got_v == want_v, (fi, field, got)


def check_clean(raw, want):
    assert make_spider()._clean_name(raw) == want, raw


def check_addr(road, number, want=None, absent=(), **kw):
    item = addressed(make_spider(), road, number, **kw)
    ex = item.get("extras") or {}

    def get(path):
        if path.startswith("extras."):
            return ex.get(path[7:])
        return item.get(path)

    for path, val in (want or {}).items():
        assert get(path) == val, (road, number, path)
    for path in absent:
        if path.startswith("extras."):
            assert path[7:] not in ex, (road, number, path)
        else:
            assert path not in item, (road, number, path)


# ---- Names: cleaning -------------------------------------------------------


@pytest.mark.parametrize(
    "raw,want",
    [
        ("Iltapäivätoiminta / Koulu, Kasvatuksen ja koulutuksen toimiala", "Iltapäivätoiminta / Koulu"),
        ("Nimi, Education Division", "Nimi"),
        ("Jorvin Terassikahvio -palvelun järjestämispaikka", "Jorvin Terassikahvio"),
        ("Nuortenillat-palvelun järjestämispaikka", "Nuortenillat"),
        ("International House Salo, palvelupaikka", "International House Salo"),
        ("Emy ry:n Hyvän mielen ryhmä", "Hyvän mielen ryhmä"),
        ("Walonkulman Klubitalo - yhteisö työikäisille", "Walonkulman Klubitalo"),
        ("Kokemäen Asiointipiste/Kela", "Kokemäen Asiointipiste"),
        ("Rikos -ja riita-asioiden sovittelua -palvelun järjestämispaikka", "Rikos -ja riita-asioiden sovittelua"),
        ("Kuntosali yhdistyksen jäsenille -palvelun järjestämispaikka", "Kuntosali yhdistyksen jäsenille"),
        ("Mustasaari, P 60° 10,343' ja I 24° 52,123'", "Mustasaari"),
        ("Seurasaari, 60°10'52'N, 024°53'05'E", "Seurasaari"),
        (
            "Nummelan kimppakävelyt Marin kanssa, yhdistyksen jäsenille. -palvelun järjestämispaikka",
            "Nummelan kimppakävelyt yhdistyksen jäsenille.",
        ),
        ("Tervetuloa tekemään käsitöitä Marttojen kanssa!", "Tervetuloa tekemään käsitöitä Marttojen kanssa!"),
        ("Elämää muistisairauden kanssa -kurssi", "Elämää muistisairauden kanssa"),
        ("Keskusteluryhmä ahdistuksen kanssa kamppaileville", "Keskusteluryhmä ahdistuksen kanssa kamppaileville"),
        ("Turun kulttuuripaja Casan yhteystiedot", "Turun kulttuuripaja Casan"),
        ("Prästgårdsbackens förskola , Gesterby", "Prästgårdsbackens förskola, Gesterby"),
        ("Päiväkoti Luomupäiväkoti Kirsikka Laajasalo", "Luomupäiväkoti Kirsikka Laajasalo"),
        ("Päiväkoti Kirsikka", "Päiväkoti Kirsikka"),
    ],
)
def test_clean_boilerplate(raw, want):
    check_clean(raw, want)


@pytest.mark.parametrize(
    "raw,want",
    [
        ("Rovastinkankaan koulun opiskeluhuolto", "Rovastinkankaan koulu"),
        ("Vammalan lukion opiskeluhuolto", "Vammalan lukio"),
        ("Ammattiopisto Spesian opiskeluhuolto", None),
        ("Opiskeluhuolto", None),
    ],
)
def test_genitive_school_mapping(raw, want):
    assert make_spider()._genitive_school(raw) == want, raw


@pytest.mark.parametrize(
    "raw,want",
    [
        ("ORIVESI AS", "ORIVESI"),
        ("ESPOO", "ESPOO"),
        (None, None),
        ("  ", None),
    ],
)
def test_post_city_station_suffix(raw, want):
    assert make_spider()._post_city(raw) == want, raw


@pytest.mark.parametrize(
    "raw,want",
    [
        ("Imatran keilahalli Oy", "Imatran keilahalli"),
        ("Sari Wicklund", None),
        ("Infopiste", None),
        ("Töölön kisahalli", "Töölön kisahalli"),
    ],
)
def test_clean_located_strips_operator_city_person(raw, want):
    assert make_spider()._clean_located(raw) == want, raw


@pytest.mark.parametrize(
    "raw,want",
    [
        ("Sipoon Enter", True),
        ("Pöytätennisalue", False),
        ("Hiekkakenttä 2", False),
        ("Imatran keilahalli Oy", False),
        ("Virtain toimipiste", False),
    ],
)
def test_is_proper_tail_guards(raw, want):
    assert make_spider()._is_proper_tail(raw) is want, raw


@pytest.mark.parametrize(
    "raw,want",
    [
        ("Kokemäen Asiointipiste/Kela", "Kela"),
        ("Tavallinen nimi", None),
        ("Kelan asiointipiste Lapinlahdella", "Kela"),
        ("Kelankatu 1", None),
        ("Siimakela", None),
    ],
)
def test_branch_agency(raw, want):
    assert make_spider()._branch_agency(raw) == want, raw


@pytest.mark.parametrize(
    "raw,want",
    [
        ("Didrichsenin taidemuseo, Kuusilahdenkuja", "Kuusilahdenkuja"),
        ("Castreninkatu, puisto", "Castreninkatu"),
        ("Rekipellonpuisto, Vesala", "Rekipellonpuisto"),
    ],
)
def test_road_base(raw, want):
    assert make_spider()._road_base(raw) == want, raw


# ---- Names: slash splits -----------------------------------------------------
# (fi, city, name, located, official, via)

_SLASH_CASES = [
    (
        "Pysäköintilippuautomaatti 222, Pengerkatu 23, korttimaksu",
        None,
        "Pysäköintilippuautomaatti 222",
        None,
        "Pysäköintilippuautomaatti 222, Pengerkatu 23, korttimaksu",
        "named",
    ),
    (
        "Pysäköintilippuautomaatti 619, Mäntymäenkenttä / 2, korttimaksu",
        None,
        "Pysäköintilippuautomaatti 619",
        None,
        PRESENT,
        "named",
    ),
    ("Pysäköintilippuautomaatti 591", None, "Pysäköintilippuautomaatti 591", None, None, "split"),
    (
        "Santahaminan ala-asteen koulu / Koripallokenttä",
        None,
        "Koripallokenttä",
        "Santahaminan ala-asteen koulu",
        PRESENT,
        "split",
    ),
    ("Meilahden yläasteen koulu / Juhlasali", None, "Juhlasali", "Meilahden yläasteen koulu", _SKIP, "split"),
    ("Kaarelankenttä / Hiekkakenttä 2", None, "Hiekkakenttä 2", "Kaarelankenttä", _SKIP, "split"),
    ("Sipoon lukio / Sipoon Enter", None, "Sipoon Enter", "Sipoon lukio", _SKIP, "split"),
    (
        "Iltapäivätoiminta / Steiner-koulu, Helsingin Rudolf Steiner-koulun kannatusyhdistys - Underst..",
        None,
        "Iltapäivätoiminta",
        "Steiner-koulu",
        PRESENT,
        "split",
    ),
    (
        "Iltapäivätoiminta / Kulosaaren ala-aste, Liikkis / Sari Wicklund",
        None,
        "Iltapäivätoiminta",
        "Kulosaaren ala-aste",
        PRESENT,
        "split",
    ),
    ("Jumppa / Sari Wicklund", None, "Jumppa", None, PRESENT, "split"),
    ("Pohjois-Espoon / Niipperin matonpesupaikka", None, "Niipperin matonpesupaikka", None, _SKIP, "split"),
    ("Uimastadion / Pöytätennisalue", None, "Pöytätennisalue", "Uimastadion", _SKIP, "split"),
    (
        "Perhekeskus Pohjatuuli / Lasten neuvola",
        None,
        "Lasten neuvola",
        "Perhekeskus Pohjatuuli",
        _SKIP,
        "split",
    ),
    (
        "Talin puttirata / Mini-Tali / Frisbeegolfin harjoittelualue",
        None,
        "Mini-Tali",
        "Talin puttirata",
        _SKIP,
        "split",
    ),
    (
        "Harjulan Setlementti ry/Liikuntapalvelut -palvelun järjestämispaikka",
        None,
        "Harjulan Setlementti ry",
        None,
        PRESENT,
        "named",
    ),
    (
        "Imatra Bowling Center / Imatran keilahalli Oy",
        None,
        "Imatra Bowling Center",
        "Imatran keilahalli",
        PRESENT,
        "split",
    ),
    ("Linnanlaituri / Vesiliikennelaituri", None, "Linnanlaituri", None, _SKIP, "split"),
    ("Lähde / UKK-muistomerkki", None, "Lähde", None, "Lähde / UKK-muistomerkki", "split"),
    ("koripallo/lentopallo", None, "koripallo/lentopallo", None, None, "split"),
    ("hiekka-/jääkenttä", None, "hiekka-/jääkenttä", None, None, "split"),
    ("Kotihoito/Vuosaari 3 lähipalvelualue", None, "Kotihoito", None, PRESENT, "split"),
    ("Kurkisuontie 2 / Hiekkakenttä", None, "Hiekkakenttä", None, "Kurkisuontie 2 / Hiekkakenttä", "split"),
    ("Kenttäpolku/Kouluravintola", None, "Kouluravintola", _SKIP, _SKIP, "split"),
    (
        "Eläintarhan urheilukenttä / Huoltorakennus 4",
        None,
        "Eläintarhan urheilukenttä",
        None,
        "Eläintarhan urheilukenttä / Huoltorakennus 4",
        "split",
    ),
    (
        "Linnunlauluntien ulkokuntosali / Ulkokuntosali",
        None,
        "Linnunlauluntien ulkokuntosali / Ulkokuntosali",
        None,
        None,
        "split",
    ),
    ("Aamulla / Vasikat", None, "Aamulla / Vasikat", None, None, "split"),
    (
        "Iltapäivätoiminta / Leikkipuisto Nurkka",
        None,
        "Iltapäivätoiminta",
        "Leikkipuisto Nurkka",
        "Iltapäivätoiminta / Leikkipuisto Nurkka",
        "split",
    ),
    (
        "Töölön seniorikeskus/Helmi ryhmäkoti",
        None,
        "Helmi ryhmäkoti",
        "Töölön seniorikeskus",
        "Töölön seniorikeskus/Helmi ryhmäkoti",
        "split",
    ),
    (
        "Keuruun yläkoulun/lukion tanssisali",
        None,
        "Keuruun yläkoulun/lukion tanssisali",
        None,
        None,
        "split",
    ),
    (
        "Hyvät Tuulet ry/MyöhäTuulen kohtaamispaikka",
        None,
        "MyöhäTuulen kohtaamispaikka",
        None,
        "Hyvät Tuulet ry/MyöhäTuulen kohtaamispaikka",
        "split",
    ),
    (
        "Harjulan Setlementti ry/Kansalaisopisto",
        None,
        "Kansalaisopisto",
        None,
        "Harjulan Setlementti ry/Kansalaisopisto",
        "split",
    ),
    (
        "Harjulan Setlementti ry/Liikuntapalvelut",
        None,
        "Harjulan Setlementti ry",
        None,
        "Harjulan Setlementti ry/Liikuntapalvelut",
        "split",
    ),
    (
        "Keurusselän ympäristön- ja terveydensuojelutoimisto / Mänttä-Vilppulan toimipiste",
        None,
        "Keurusselän ympäristön- ja terveydensuojelutoimisto / Mänttä-Vilppulan toimipiste",
        None,
        None,
        "split",
    ),
    ("Puheterapia / Tikkurilan alue", None, "Puheterapia / Tikkurilan alue", None, None, "split"),
    ("Fysioterapia / Himangan yksikkö", None, "Fysioterapia / Himangan yksikkö", None, None, "split"),
    ("Tahvonlahti / Hiekkakenttä", None, "Hiekkakenttä", "Tahvonlahti", "Tahvonlahti / Hiekkakenttä", "split"),
    (
        "Töölönlahti / WDC-ulkokuntoilupaikka 1",
        None,
        "WDC-ulkokuntoilupaikka 1",
        "Töölönlahti",
        "Töölönlahti / WDC-ulkokuntoilupaikka 1",
        "split",
    ),
    ("Lahti / Matkustajasatama", None, "Lahti / Matkustajasatama", None, None, "split"),
    ("Kahvila / Ulkoilusaari", None, "Kahvila", "Ulkoilusaari", "Kahvila / Ulkoilusaari", "split"),
    ("Suomenlinna / Kalastuspaikka", None, "Kalastuspaikka", "Suomenlinna", _SKIP, "split"),
    ("Moduli / Rakentajaveistos", None, "Moduli / Rakentajaveistos", None, None, "split"),
    (
        "Salmen ulkoilualue (Pikku-Parikas) / Kalastuspaikka",
        None,
        "Kalastuspaikka",
        "Salmen ulkoilualue (Pikku-Parikas)",
        _SKIP,
        "split",
    ),
    (
        "Kaunissaari / Telttailu- ja leiriytymispaikka 2.",
        None,
        "Telttailu- ja leiriytymispaikka 2.",
        "Kaunissaari",
        _SKIP,
        "split",
    ),
    ("Väinämöisenkenttä / Huoltorakennus", None, "Väinämöisenkenttä", _SKIP, _SKIP, "named"),
    (
        "Sateenkaari Koto Oy/ Villasukka",
        None,
        "Villasukka",
        None,
        "Sateenkaari Koto Oy/ Villasukka",
        "split",
    ),
    (
        "Iltapäivätoiminta / Kottby grundskola, Kottbynejdens svenska förening rf",
        None,
        "Iltapäivätoiminta",
        "Kottby grundskola",
        "Iltapäivätoiminta / Kottby grundskola, Kottbynejdens svenska förening rf",
        "split",
    ),
    (
        "Kerho / Koulu, Tmi Petri Lehto",
        None,
        "Kerho",
        "Koulu",
        "Kerho / Koulu, Tmi Petri Lehto",
        "split",
    ),
    ("Vihdin kunnantalo/Keskusta", None, "Vihdin kunnantalo/Keskusta", None, None, "split"),
    (
        "Vihdin kunnantalo/sosiaalitoimisto",
        None,
        "sosiaalitoimisto",
        "Vihdin kunnantalo",
        "Vihdin kunnantalo/sosiaalitoimisto",
        "split",
    ),
    (
        "Vihdin kunnantalo/Sote-keskus Länsi",
        None,
        "Sote-keskus Länsi",
        "Vihdin kunnantalo",
        "Vihdin kunnantalo/Sote-keskus Länsi",
        "split",
    ),
    (
        "Vuoniityn peruskoulu / Lähiliikuntapaikka",
        None,
        "Lähiliikuntapaikka",
        "Vuoniityn peruskoulu",
        "Vuoniityn peruskoulu / Lähiliikuntapaikka",
        "named",
    ),
    (
        "Myllypuron peruskoulu / Lähiliikuntapaikka 2",
        None,
        "Lähiliikuntapaikka 2",
        "Myllypuron peruskoulu",
        "Myllypuron peruskoulu / Lähiliikuntapaikka 2",
        "named",
    ),
    (
        "Leikkipuisto Lampi / Lähiliikuntapaikka",
        None,
        "Leikkipuisto Lampi",
        "Lähiliikuntapaikka",
        "Leikkipuisto Lampi / Lähiliikuntapaikka",
        "named",
    ),
    (
        "Hietarannan uimaranta / Koripallokenttä",
        None,
        "Koripallokenttä",
        "Hietarannan uimaranta",
        "Hietarannan uimaranta / Koripallokenttä",
        "named",
    ),
    (
        "Väinämöisenkenttä / Ulkokuntoilupaikka",
        None,
        "Ulkokuntoilupaikka",
        "Väinämöisenkenttä",
        "Väinämöisenkenttä / Ulkokuntoilupaikka",
        "named",
    ),
    (
        "Hietarannan uimaranta / Ulkokuntoilupaikka (Keski)",
        None,
        "Ulkokuntoilupaikka (Keski)",
        "Hietarannan uimaranta",
        "Hietarannan uimaranta / Ulkokuntoilupaikka (Keski)",
        "named",
    ),
    (
        "Malmitalo / Esiintymisali (Pieni sali)",
        None,
        "Esiintymisali (Pieni sali)",
        "Malmitalo",
        "Malmitalo / Esiintymisali (Pieni sali)",
        "named",
    ),
    ("Stoan aukio / Grillipaikka", None, "Grillipaikka", "Stoan aukio", "Stoan aukio / Grillipaikka", "named"),
    ("Tullisaari / Grillipaikka", None, "Grillipaikka", "Tullisaari", "Tullisaari / Grillipaikka", "named"),
    (
        "Koskelan monipuolinen palvelukeskus / Hoitoalan ruokapalvelut",
        None,
        "Hoitoalan ruokapalvelut",
        "Koskelan monipuolinen palvelukeskus",
        "Koskelan monipuolinen palvelukeskus / Hoitoalan ruokapalvelut",
        "split",
    ),
    (
        "Pikku Huopalahden ala-asteen koulu / Koripallon heittopaikka",
        None,
        "Koripallon heittopaikka",
        "Pikku Huopalahden ala-asteen koulu",
        "Pikku Huopalahden ala-asteen koulu / Koripallon heittopaikka",
        "split",
    ),
    (
        "Sivistysosasto / Koulutus",
        None,
        "Sivistysosasto / Koulutus",
        _SKIP,
        _SKIP,
        "named",
    ),
    ("Vihdin kunnantalo/ sosiaalitoimisto", "Vihti", "sosiaalitoimisto", _SKIP, _SKIP, "named"),
    ("Rakennusvalvontatoimisto/lupasihteeri", None, "Rakennusvalvontatoimisto", _SKIP, _SKIP, "named"),
    (
        "Roihuvuoren seniorikeskus/Liina päivätoiminta 2*",
        "Helsinki",
        "Liina päivätoiminta 2",
        "Roihuvuoren seniorikeskus",
        "Roihuvuoren seniorikeskus/Liina päivätoiminta 2",
        "named",
    ),
    ("Peliryhmä Kuopio -palvelun järjestämispaikka", "Kuopio", "Peliryhmä", _SKIP, _SKIP, "named"),
    (
        "Pilke päiväkodit Oy/ Musiikkipäiväkoti Sinikello (Tuureporinkatu 5 E)",
        None,
        "Musiikkipäiväkoti Sinikello",
        None,
        PRESENT,
        "named",
    ),
]


@pytest.mark.parametrize("fi,city,name,located,official,via", _SLASH_CASES)
def test_name_slash(fi, city, name, located, official, via):
    check_split(fi, city, name, located, official, via)


def test_slash_person_sharing_school_token_kept():
    # Host-named units share a token with their school: the person guard
    # must not eat them.
    spider = make_spider()
    assert spider._is_person("Sari Wicklund") is True
    name, located, _ = split(spider, "Sipoon lukio / Sipoon Enter")
    assert (name, located) == ("Sipoon Enter", "Sipoon lukio")


@pytest.mark.parametrize(
    "raw,want",
    [
        ("Steiner-koulu, Helsingin Rudolf Steiner -yhdistys", "Steiner-koulu"),
        ("Koulu, Tmi Petri Lehto", "Koulu"),
    ],
)
def test_strip_venue_org(raw, want):
    assert make_spider()._strip_venue_org(raw) == want, raw


# ---- Names: comma splits -------------------------------------------------------
# (fi, city, name, located, official, via)

_COMMA_CASES = [
    ("Opiskeluhuolto, Karhusuon koulu", None, "Opiskeluhuolto", "Karhusuon koulu", _SKIP, "split"),
    (
        "Rovastinkankaan koulun opiskeluhuolto, Orivesi",
        "Orivesi",
        "Opiskeluhuolto",
        "Rovastinkankaan koulu",
        PRESENT,
        "split",
    ),
    (
        "Ammattiopisto Spesian opiskeluhuolto, Salo",
        "Salo",
        "Ammattiopisto Spesian opiskeluhuolto",
        None,
        PRESENT,
        "split",
    ),
    ("Kiikoisten lähitori, Sastamala", "Sastamala", "Kiikoisten lähitori", None, PRESENT, "split"),
    (
        "Mäntymäen perhetukikeskus, Turku",
        "Helsinki",
        "Mäntymäen perhetukikeskus, Turku",
        None,
        None,
        "split",
    ),
    ("Vaasa, Ulosottolaitos", "Vaasa", "Ulosottolaitos", None, PRESENT, "split"),
    # Municipality tails are never rooms; bilingual cities match either form.
    ("Maarianhamina, Ulosottolaitos", "Maarianhamina - Mariehamn", "Ulosottolaitos", None, PRESENT, "split"),
    ("Perheneuvola, Laitila", "Laitila", "Perheneuvola", None, PRESENT, "split"),
    ("Laitilan terveysasema, Laitila", "Laitila", "Laitilan terveysasema", None, PRESENT, "split"),
    ("Marttilan sote-piste, Marttila", "Marttila", "Marttilan sote-piste", None, PRESENT, "split"),
    (
        "Lasten puheterapia, Perhekeskus Pohjatuuli",
        None,
        "Lasten puheterapia",
        "Perhekeskus Pohjatuuli",
        _SKIP,
        "split",
    ),
    (
        "Myllypuron seniorikeskus, ryhmäkoti Sonaatti",
        None,
        "Ryhmäkoti Sonaatti",
        "Myllypuron seniorikeskus",
        _SKIP,
        "split",
    ),
    (
        "Eurooppalainen koulu European Schooling Helsinki, kouluterveydenhuolto",
        None,
        "Kouluterveydenhuolto",
        "Eurooppalainen koulu European Schooling Helsinki",
        _SKIP,
        "split",
    ),
    (
        "Tehostetun avohoidon yksikkö, Lohjan sairaala",
        None,
        "Tehostetun avohoidon yksikkö",
        "Lohjan sairaala",
        _SKIP,
        "split",
    ),
    (
        "Kouluravintola, Pihlajamäen ala-asteen koulu",
        None,
        "Kouluravintola",
        "Pihlajamäen ala-asteen koulu",
        _SKIP,
        "split",
    ),
    ("Nuorisopsykiatrian osasto J1, Tyks", None, "Nuorisopsykiatrian osasto J1", None, _SKIP, "split"),
    ("Kotihoito, Oulainen ja Merijärvi", None, "Kotihoito", None, PRESENT, "split"),
    ("Katriinan toimipiste, osasto 5", None, "Katriinan toimipiste, osasto 5", None, None, "split"),
    ("Katriinan toimipiste, osasto 7", "Vantaa", "Katriinan toimipiste, osasto 7", _SKIP, _SKIP, "named"),
    (
        "Attendo Ukko-Pekka, Humppila, yhteisöllisen asumisen ostopalvelut",
        None,
        "Attendo Ukko-Pekka, Humppila",
        None,
        PRESENT,
        "split",
    ),
    (
        "Pohjanmaan elinvoimakeskus, Kokkolan toimipaikka",
        None,
        "Pohjanmaan elinvoimakeskus, Kokkolan toimipaikka",
        None,
        None,
        "split",
    ),
    (
        "Koskelan ala-asteen koulu, Mäkelänkatu 84",
        None,
        "Koskelan ala-asteen koulu",
        None,
        PRESENT,
        "split",
    ),
    ("Neuvonta, Reimasali", None, "Neuvonta", "Reimasali", _SKIP, "split"),
    ("Sipoon lukio, Enter", None, "Enter", "Sipoon lukio", _SKIP, "split"),
    ("Neuvonta,", None, "Neuvonta", None, "Neuvonta,", "split"),
    ("Vaajakummun koulu, luistelukenttä", None, "luistelukenttä", "Vaajakummun koulu", _SKIP, "split"),
    (
        "Kouluravintola, Pukinmäenkaaren peruskoulu, Kenttäpolku",
        None,
        "Kouluravintola, Pukinmäenkaaren peruskoulu",
        None,
        "Kouluravintola, Pukinmäenkaaren peruskoulu, Kenttäpolku",
        "split",
    ),
    (
        "Vojakkalan uimapaikka, Kaartjärvi",
        None,
        "Vojakkalan uimapaikka",
        "Kaartjärvi",
        "Vojakkalan uimapaikka, Kaartjärvi",
        "split",
    ),
    (
        "Kahluuallas, Leikkipuisto Traktori",
        None,
        "Kahluuallas",
        "Leikkipuisto Traktori",
        "Kahluuallas, Leikkipuisto Traktori",
        "split",
    ),
    ("Puheterapia, Tikkurilan alue", "Vantaa", "Puheterapia, Tikkurilan alue", None, None, "split"),
    ("Fysioterapia, Himangan yksikkö", "Kalajoki", "Fysioterapia, Himangan yksikkö", None, None, "split"),
    ("Mannerheimin muistomerkki, Helsinki", None, "Mannerheimin muistomerkki, Helsinki", None, None, "split"),
    (
        "Kuntoutusohjaus, Kaarina, Lieto",
        "Kaarina",
        "Kuntoutusohjaus",
        None,
        "Kuntoutusohjaus, Kaarina, Lieto",
        "split",
    ),
    (
        "Esiopetuksen opiskeluhuolto, Norlandia Linna",
        None,
        "Esiopetuksen opiskeluhuolto",
        "Norlandia Linna",
        "Esiopetuksen opiskeluhuolto, Norlandia Linna",
        "split",
    ),
    (
        "Zacharias Topeliusskolan, Smågruppsundervisning",
        None,
        "Smågruppsundervisning",
        "Zacharias Topeliusskolan",
        _SKIP,
        "split",
    ),
    (
        "Opiskeluhuolto, Karis svenska högstadium",
        None,
        "Opiskeluhuolto",
        "Karis svenska högstadium",
        _SKIP,
        "split",
    ),
    (
        "Kouluravintola, Merilahden peruskoulu, Kallvikinniementien toimipiste",
        "Helsinki",
        "Kouluravintola",
        "Merilahden peruskoulu, Kallvikinniementien toimipiste",
        "Kouluravintola, Merilahden peruskoulu, Kallvikinniementien toimipiste",
        "named",
    ),
    (
        "Merilahden peruskoulu, Jaluspolun toimipiste, kouluterveydenhuolto",
        None,
        "Kouluterveydenhuolto",
        "Merilahden peruskoulu, Jaluspolun toimipiste",
        "Merilahden peruskoulu, Jaluspolun toimipiste, kouluterveydenhuolto",
        "named",
    ),
    (
        "Raskauden seurantaosasto, Tyks Majakkasairaala, Turku",
        "Turku",
        "Raskauden seurantaosasto",
        "Tyks Majakkasairaala",
        "Raskauden seurantaosasto, Tyks Majakkasairaala, Turku",
        "split",
    ),
    (
        "Lasten ja nuorten osasto, Ahveniston sairaala",
        None,
        "Lasten ja nuorten osasto",
        "Ahveniston sairaala",
        "Lasten ja nuorten osasto, Ahveniston sairaala",
        "split",
    ),
    (
        "Lastensuojelun jälkihuolto, mm. Iisalmi, Keitele",
        None,
        "Lastensuojelun jälkihuolto",
        None,
        "Lastensuojelun jälkihuolto, mm. Iisalmi, Keitele",
        "split",
    ),
    (
        "Opiskeluterveydenhuolto, keskitetty palvelu Espoo ja Kauniainen",
        None,
        "Opiskeluterveydenhuolto, keskitetty palvelu Espoo ja Kauniainen",
        None,
        None,
        "split",
    ),
    (
        "Ravitsemusterapia, Kustavi, Laitila, Masku, Mynämäki, Naantali, Nousiainen",
        None,
        "Ravitsemusterapia",
        None,
        "Ravitsemusterapia, Kustavi, Laitila, Masku, Mynämäki, Naantali, Nousiainen",
        "split",
    ),
    ("Ravintola, Lahti", None, "Ravintola, Lahti", None, None, "split"),
    (
        "Neuvonta, Reimasali, Lahti",
        None,
        "Neuvonta",
        "Reimasali",
        "Neuvonta, Reimasali, Lahti",
        "split",
    ),
    (
        "Vertaistukea Parkinsonia sairastavalle, K-U:lla",
        None,
        "Vertaistukea Parkinsonia sairastavalle",
        None,
        _SKIP,
        "split",
    ),
    (
        "Naisten kuntosaliryhmä, Kaukajärven vapaa-aika talo",
        None,
        "Naisten kuntosaliryhmä",
        "Kaukajärven vapaa-aika talo",
        "Naisten kuntosaliryhmä, Kaukajärven vapaa-aika talo",
        "named",
    ),
    (
        "Avustajakurssi, Pori - vapaaehtoistoimintaan mukaan!",
        "Pori",
        "Avustajakurssi",
        None,
        "Avustajakurssi, Pori - vapaaehtoistoimintaan mukaan!",
        "named",
    ),
    (
        "Pirkanmaan oikeusaputoimisto, Valkeakosken vastaanotto",
        None,
        "Pirkanmaan oikeusaputoimisto, Valkeakosken vastaanotto",
        None,
        None,
        "split",
    ),
    ("Tampereen kaupunki, Vastaanotto", None, "Tampereen kaupunki, Vastaanotto", None, None, "split"),
    ("Kalvolan neuvola, Iittala", None, "Kalvolan neuvola, Iittala", None, None, "split"),
    (
        "Fysioterapia Pori, Länsi-Porin sote-keskus",
        "Pori",
        "Fysioterapia",
        "Länsi-Porin sote-keskus",
        "Fysioterapia Pori, Länsi-Porin sote-keskus",
        "split",
    ),
    ("Arvi Pori", "Pori", "Arvi Pori", None, None, "split"),
    ("Renkomäen koulun luokat Lahti", "Lahti", "Luokat", "Renkomäen koulu", "Renkomäen koulun luokat Lahti", "split"),
    (
        "Työllistymistä edistävät palvelut, Masku (Nousiainen, Laitila)",
        "Masku",
        "Työllistymistä edistävät palvelut",
        _SKIP,
        _SKIP,
        "named",
    ),
    (
        "Ilveskodin päivätoiminta, Hämeenlinna, Vammaisten päivätoiminta",
        "Hämeenlinna",
        "Ilveskodin päivätoiminta",
        None,
        _SKIP,
        "named",
    ),
    (
        "Kulttuuria, kahvetta ja kastamista Kiikassa -palvelun järjestämispaikka",
        "Sastamala",
        "Kulttuuria, kahvetta ja kastamista Kiikassa",
        _SKIP,
        _SKIP,
        "named",
    ),
    (
        "Pyhämäntie, Janakkala, Vammaisten asumispalvelut",
        "Janakkala",
        "Vammaisten asumispalvelut",
        None,
        "Pyhämäntie, Janakkala, Vammaisten asumispalvelut",
        "split",
    ),
    (
        "Perheoikeudelliset palvelut perhekeskus Pohjatuuli (Karvia, Siikainen, Pomarkku, Kankaanpää, Jämijärvi)",
        "Kankaanpää",
        "Perheoikeudelliset palvelut perhekeskus Pohjatuuli",
        None,
        "Perheoikeudelliset palvelut perhekeskus Pohjatuuli (Karvia, Siikainen, Pomarkku, Kankaanpää, Jämijärvi)",
        "split",
    ),
    (
        "Perheoikeudelliset palvelut perhekeskus X (Karvia, Pomarkku)",
        "Pori",
        "Perheoikeudelliset palvelut perhekeskus X",
        "Karvia, Pomarkku",
        "Perheoikeudelliset palvelut perhekeskus X (Karvia, Pomarkku)",
        "split",
    ),
    (
        "Vertaistukiryhmä | Uskontojen uhrien tuki Uut ry | Kokkola",
        "Kokkola",
        "Vertaistukiryhmä | Uskontojen uhrien tuki Uut ry",
        _SKIP,
        _SKIP,
        "split",
    ),
    ("Touhula Helmiina (yksityinen päiväkoti)", "Ylivieska", _SKIP, None, _SKIP, "named"),
]


@pytest.mark.parametrize("fi,city,name,located,official,via", _COMMA_CASES)
def test_name_comma(fi, city, name, located, official, via):
    check_split(fi, city, name, located, official, via)


# ---- Names: parens, dashes, colons, city tails --------------------------------
# (fi, city, name, located, official, via); _NAME_ONLY rows pin [0] only.

_PAREN_DASH_CASES = [
    (
        "Luustoyhdistyksen vesijumppa Helsingissä (Oltermannikeskus)",
        None,
        "Luustoyhdistyksen vesijumppa Helsingissä",
        "Oltermannikeskus",
        PRESENT,
        "split",
    ),
    ("Mäntymäen päiväkoti (Kallelankatu 3)", None, "Mäntymäen päiväkoti", _SKIP, _SKIP, "split"),
    ("Totto-Halli (Muurola)", None, "Totto-Halli", _SKIP, _SKIP, "split"),
    (
        "Musiikkipäiväkoti Sinikello (Tuureporinkatu 5 E)",
        None,
        "Musiikkipäiväkoti Sinikello",
        None,
        "Musiikkipäiväkoti Sinikello (Tuureporinkatu 5 E)",
        "split",
    ),
    ("Daycare Daisy Oy (Ylioppilaskatu 25)", None, "Daycare Daisy Oy", _SKIP, _SKIP, "split"),
    ("Friemanin talo - nuorisotoimisto", None, "Nuorisotoimisto", "Friemanin talo", PRESENT, "split"),
    ("Malminkartano - Pitäjänmäki", None, _SKIP, None, _SKIP, "split"),
    ("OYSin Keuhkosairauksien poliklinikka", None, "Keuhkosairauksien poliklinikka", None, PRESENT, "split"),
    ("Kuntoilulaitteet (ulko)", None, "Kuntoilulaitteet (ulko)", None, None, "split"),
    (
        "Kottby grundskola, Arabia kvartersskola, åk 1–2",
        None,
        "Kottby grundskola, Arabia kvartersskola, åk 1–2",
        None,
        None,
        "split",
    ),
    (
        "Sovellettua jooga-, pilates- ja faskiaharjoittelua Tesoma",
        None,
        "Sovellettua jooga-, pilates- ja faskiaharjoittelua Tesoma",
        None,
        None,
        "split",
    ),
    (
        "Virkeät Ikämiehet -toiminnan starttikurssi Sastamala",
        None,
        "Virkeät Ikämiehet -toiminnan starttikurssi Sastamala",
        _SKIP,
        _SKIP,
        "split",
    ),
    (
        "Kuivalahden koulun 5 -väyläinen frisbeegolfrata",
        None,
        "Kuivalahden koulun 5 -väyläinen frisbeegolfrata",
        _SKIP,
        _SKIP,
        "split",
    ),
    ("Ulkokuntoilusalit ja -alueet", None, "Ulkokuntoilusalit ja -alueet", _SKIP, _SKIP, "split"),
    ("Outokumpu: Vertaisryhmä", "Outokumpu", "Vertaisryhmä", None, "Outokumpu: Vertaisryhmä", "split"),
    (
        "OLKA-pisteen teemapäivä: Saimaan Syöpäyhdistys ry",
        None,
        "OLKA-pisteen teemapäivä",
        None,
        "OLKA-pisteen teemapäivä: Saimaan Syöpäyhdistys ry",
        "split",
    ),
    ("Kuntoutusohjaus Kankaanpää", "Kankaanpää", "Kuntoutusohjaus", None, "Kuntoutusohjaus Kankaanpää", "split"),
    ("Toimintakeskus Parikkala", "Parikkala", "Toimintakeskus", _SKIP, _SKIP, "split"),
    (
        "Martat neuvoo Kuusankosken kirjastossa",
        None,
        "Martat neuvoo",
        "Kuusankosken kirjasto",
        "Martat neuvoo Kuusankosken kirjastossa",
        "split",
    ),
    (
        "Yhteisökahvila Hollolan uimahallilla",
        None,
        "Yhteisökahvila",
        "Hollolan uimahalli",
        "Yhteisökahvila Hollolan uimahallilla",
        "split",
    ),
    (
        "Lohjan Sydän digiopastusta Lohjan pääkirjastossa",
        None,
        "Lohjan Sydän digiopastusta",
        "Lohjan pääkirjasto",
        "Lohjan Sydän digiopastusta Lohjan pääkirjastossa",
        "named",
    ),
    (
        "Martat neuvoo Haminan kirjastossa",
        None,
        "Martat neuvoo",
        "Haminan kirjasto",
        "Martat neuvoo Haminan kirjastossa",
        "named",
    ),
    (
        "Neuvonta Myyrmäen neuvolassa",
        None,
        "Neuvonta",
        "Myyrmäen neuvola",
        "Neuvonta Myyrmäen neuvolassa",
        "split",
    ),
    (
        "Koulutusinfo Kuusankosken kirjastossa",
        None,
        "Koulutusinfo",
        "Kuusankosken kirjasto",
        "Koulutusinfo Kuusankosken kirjastossa",
        "split",
    ),
    (
        "Digiopastusta ikäihmisille Tesoman kirjastossa -palvelun järjestämispaikka",
        None,
        "Digiopastusta ikäihmisille",
        "Tesoman kirjasto",
        _SKIP,
        "named",
    ),
    ("Päiväkoti Peukalopotti (lakkautettu)", None, "Päiväkoti Peukalopotti", _SKIP, _SKIP, "split"),
    ("Virkkalan päiväkoti (väistö)", None, "Virkkalan päiväkoti", _SKIP, _SKIP, "split"),
    (
        "Hanhikosken ryhmäperhepäivähoito (toiminta loppunut 31.7.2024)",
        None,
        "Hanhikosken ryhmäperhepäivähoito",
        _SKIP,
        _SKIP,
        "split",
    ),
    (
        "Luoteis-Savon Maaseutupalvelut - Kiuruveden maataloustoimisto",
        None,
        "Luoteis-Savon Maaseutupalvelut - Kiuruveden maataloustoimisto",
        None,
        None,
        "split",
    ),
    (
        "Juhananpuiston leikkipaikka (Idänpää)",
        "Hämeenlinna",
        "Juhananpuiston leikkipaikka (Idänpää)",
        None,
        None,
        "split",
    ),
    (
        "Ylivieskan oikeusaputoimisto, Haapaveden toimipaikka (vain ajanvarauksella)",
        None,
        "Ylivieskan oikeusaputoimisto, Haapaveden toimipaikka",
        None,
        "Ylivieskan oikeusaputoimisto, Haapaveden toimipaikka (vain ajanvarauksella)",
        "split",
    ),
    (
        "Kirjasto (Pääkirjasto) (Keskusta)",
        None,
        "Kirjasto",
        "Pääkirjasto",
        "Kirjasto (Pääkirjasto) (Keskusta)",
        "split",
    ),
    ("Kirjasto (Sali 2)", None, "Sali 2", "Kirjasto", "Kirjasto (Sali 2)", "split"),
    ("Pallokenttä - Sali 2", None, "Sali 2", "Pallokenttä", "Pallokenttä - Sali 2", "split"),
    (
        "Kaukajärven koulu - Koulutusinfo",
        None,
        "Koulutusinfo",
        "Kaukajärven koulu",
        "Kaukajärven koulu - Koulutusinfo",
        "split",
    ),
    (
        "Kaukajärven koulu - Annalan koulutalo",
        None,
        "Kaukajärven koulu - Annalan koulutalo",
        None,
        None,
        "split",
    ),
    (
        "Espoonlahden koulun ja lukion liikuntasali",
        None,
        "Espoonlahden koulun ja lukion liikuntasali",
        None,
        None,
        "split",
    ),
    (
        "Renkomäen koulun vaativan monimuotoisen tuen luokat",
        None,
        "Vaativan monimuotoisen tuen luokat",
        "Renkomäen koulu",
        "Renkomäen koulun vaativan monimuotoisen tuen luokat",
        "split",
    ),
    (
        "Vanha Ulvilan koulun liikuntasali",
        None,
        "Liikuntasali",
        "Vanha Ulvilan koulu",
        "Vanha Ulvilan koulun liikuntasali",
        "split",
    ),
    (
        "Tampereen kansainvälisen koulun (FISTA) opiskeluhuolto",
        None,
        "Tampereen kansainvälisen koulun (FISTA) opiskeluhuolto",
        None,
        None,
        "split",
    ),
    (
        "Tila - Herralan koulu - Liikuntasali",
        None,
        "Tila - Herralan koulu - Liikuntasali",
        None,
        None,
        "split",
    ),
    (
        "Rantafutis - ja käsipallokenttä",
        None,
        "Rantafutis - ja käsipallokenttä",
        None,
        None,
        "split",
    ),
    (
        "Sydänpiste - tietoa ja tukea sydänpotilaalle",
        None,
        "Sydänpiste - tietoa ja tukea sydänpotilaalle",
        None,
        None,
        "split",
    ),
    ("Tila - Koskihalli", None, "Tila - Koskihalli", None, None, "split"),
    (
        "Kuntoutusohjaus Mänttä-Vilppula",
        "Mänttä-Vilppula",
        "Kuntoutusohjaus",
        None,
        "Kuntoutusohjaus Mänttä-Vilppula",
        "split",
    ),
    ("Päiväkoti Pikku-Elli", "Helsinki", "Päiväkoti Pikku-Elli", None, None, "split"),
    ("Nurmeksen poliisiasema, löytötavarat", None, "Nurmeksen poliisiasema, löytötavarat", None, None, "split"),
    ("Kuhmon poliisiasema, asetarkastus", None, "Kuhmon poliisiasema, asetarkastus", None, None, "split"),
    (
        "Pietarsaaren poliisiasema, aseen esitys",
        None,
        "Pietarsaaren poliisiasema, aseen esitys",
        None,
        None,
        "split",
    ),
    (
        "Loimaan poliisiasema, poliisipäivystys",
        None,
        "Loimaan poliisiasema, poliisipäivystys",
        None,
        None,
        "split",
    ),
    ("Maanmittauslaitos Oulu", "Oulu", "Maanmittauslaitos", None, "Maanmittauslaitos Oulu", "split"),
    ("Maanmittauslaitos Ivalo", "Inari", "Maanmittauslaitos Ivalo", None, None, "split"),
    (
        "Päiväkoti International School of Helsinki",
        "Helsinki",
        "Päiväkoti International School of Helsinki",
        None,
        None,
        "split",
    ),
    ("SavoGrow Pielavesi", "Pielavesi", "SavoGrow Pielavesi", None, None, "split"),
    (
        "Avoin jumpparyhmä Kouvola",
        "Kouvola",
        "Avoin jumpparyhmä",
        None,
        "Avoin jumpparyhmä Kouvola",
        "split",
    ),
    ("Helsinge skolan liikuntasali", None, "Helsinge skolan liikuntasali", None, None, "split"),
    ("Lagstads skolan liikuntasali 2", None, "Lagstads skolan liikuntasali 2", None, None, "split"),
    ("International House Rauma", "Rauma", "International House Rauma", None, None, "split"),
]


@pytest.mark.parametrize("fi,city,name,located,official,via", _PAREN_DASH_CASES)
def test_name_paren_dash_colon_city(fi, city, name, located, official, via):
    check_split(fi, city, name, located, official, via)


def test_split_name_never_returns_none():
    # Totality: adversarial punctuation must never crash the unpack in
    # _apply_naming (trailing-comma batch killer precedent).
    spider = make_spider()
    for probe in ("Neuvonta,", ",", " , ", "Kotihoito, ", "/", " / ", "A / B /", ",,,", "Nimi (", "Nimi ()"):
        result = spider._split_name(spider._clean_name(probe), None)
        assert result is not None and len(result) == 3, probe


def test_city_prefix_only_strips_services():
    # Salo-Karinan neuvonta-asema: proper compounds stay whole.
    item = parsed(make_spider(), channel("Salo-Karinan neuvonta-asema", office="SALO"))
    assert item["name"] == "Salo-Karinan neuvonta-asema"
    assert item.get_tag("office") == "government"


def test_trailing_comma_names_head_and_totality():
    # Trailing-comma batch killer: head names it, signed form survives;
    # SYNTHETIC dangling shape included.
    spider = make_spider()
    item = parsed(
        spider,
        channel("Hae mukaan Hyvän olon polku -ryhmään! -palvelun järjestämispaikka,"),
        "Jyväskylän kaupunki",
    )
    assert item["name"] == "Hae mukaan Hyvän olon polku -ryhmään!"
    assert item["extras"]["official_name"] == "Hae mukaan Hyvän olon polku -ryhmään! -palvelun järjestämispaikka,"


# ---- Addresses -------------------------------------------------------------------
# (road, number, kw, want, absent)

_ADDR_CASES = [
    (
        "Lummetie",
        "2B, A rappu",
        {},
        {"street": "Lummetie", "housenumber": "2b", "extras.addr:unit": "A rappu"},
        ("street_address",),
    ),
    ("Katu", "3A", {}, {"street": "Katu", "housenumber": "3a"}, ("street_address", "extras.addr:unit")),
    # Range halves lowercase together with the plot letter.
    ("Katu", "12A-14B", {}, {"street": "Katu", "housenumber": "12a-14b"}, ("street_address", "extras.addr:unit")),
    (
        "Kielotie",
        "7 A, 2.kerros",
        {},
        {"street": "Kielotie", "housenumber": "7", "extras.addr:unit": "A", "extras.addr:floor": "2"},
        ("street_address", "extras.level"),
    ),
    ("Kolpintie", "7, PL 111", {}, {"street": "Kolpintie", "housenumber": "7"}, ("street_address", "extras.addr:unit")),
    ("Tie", "14 / Espoon Keskuspuisto", {}, {"street": "Tie", "housenumber": "14"}, ()),
    ("Tie", "4 / Espoon Keskuspuisto", {}, {"street": "Tie", "housenumber": "4"}, ()),
    ("Tie", "70, Töölö", {}, {"street": "Tie", "housenumber": "70"}, ()),
    (
        "Kunnallissairaalantie",
        "20, rakennus 7",
        {},
        {"street": "Kunnallissairaalantie", "housenumber": "20", "extras.addr:unit": "rakennus 7"},
        ("street_address",),
    ),
    (
        "Tie",
        "2, A-ovi, 2. krs",
        {},
        {"street": "Tie", "housenumber": "2", "extras.addr:unit": "A-ovi", "extras.addr:floor": "2"},
        ("street_address",),
    ),
    ("Hallintoaukio", "0", {}, {"extras.addr:place": "Hallintoaukio"}, ("street_address",)),
    (
        "Veräjäpellonkatu / Kaivoskallionpolku",
        "",
        {},
        {"addr_full": "Veräjäpellonkatu / Kaivoskallionpolku"},
        (),
    ),
    ("Tiirakari", "", {}, {"extras.addr:place": "Tiirakari"}, ("street_address",)),
    ("Urho Kekkosen katu", "", {}, {"street": "Urho Kekkosen katu"}, ("housenumber", "street_address")),
    (
        "Katu",
        "1",
        {"postcode": "00100", "office": "ESPOO"},
        {"postcode": "00100", "city": "Espoo", "country": "FI"},
        (),
    ),
    ("Katu", "1", {"office": "ORIVESI AS"}, {"city": "Orivesi"}, ()),
    (
        "Arabianpolku",
        "1A2",
        {},
        {"street": "Arabianpolku", "housenumber": "1a", "extras.addr:unit": "2"},
        ("street_address",),
    ),
    ("Nummentie", "12 - 14", {}, {"street": "Nummentie", "housenumber": "12-14"}, ()),
    (
        "Pursimiehenkatu",
        "8 52 A",
        {},
        {"street": "Pursimiehenkatu", "housenumber": "8", "extras.addr:unit": "52 A"},
        ("street_address",),
    ),
    ("Katu", "5 A", {}, {"street": "Katu", "housenumber": "5", "extras.addr:unit": "A"}, ("street_address",)),
    ("Krakantien päässä", "", {}, {"addr_full": "Krakantien päässä"}, ()),
    (
        "Voimapolku",
        "3 03100 Nummela",
        {"postcode": "03100", "office": "NUMMELA"},
        {"street": "Voimapolku", "housenumber": "3"},
        (),
    ),
    ("Sankarinkurvi", "", {}, {"street": "Sankarinkurvi"}, ("street_address",)),
    ("wetterhoffinkatu", "2", {}, {"street": "Wetterhoffinkatu", "housenumber": "2"}, ()),
    ("Painiityntie", "21 ja 21", {}, {"street": "Painiityntie", "housenumber": "21"}, ()),
    (
        "Leonkatu",
        "4 Liiketila 3B-120",
        {},
        {"street": "Leonkatu", "housenumber": "4", "extras.addr:unit": "Liiketila 3B-120"},
        ("street_address",),
    ),
    ("Katu", "1, B", {}, {"street": "Katu", "housenumber": "1", "extras.addr:unit": "B"}, ()),
    (
        "Laivalahdenkatu",
        "2B, B",
        {},
        {"street": "Laivalahdenkatu", "housenumber": "2b"},
        ("street_address", "extras.addr:unit"),
    ),
    (
        "Katu",
        "1, 2 vån",
        {},
        {"street": "Katu", "housenumber": "1", "extras.addr:floor": "2"},
        (),
    ),
    (
        "Tie",
        "7 A (3. kerros)",
        {},
        {"street": "Tie", "housenumber": "7", "extras.addr:unit": "A", "extras.addr:floor": "3"},
        ("extras.level",),
    ),
    (
        "Tie",
        "7 A (kolmas kerros)",
        {},
        {"street": "Tie", "housenumber": "7", "extras.addr:unit": "A", "extras.addr:floor": "3"},
        ("extras.level",),
    ),
    ("Katu", "4 a, toinen. krs", {}, {"extras.addr:floor": "2"}, ("extras.level",)),
    ("Tie", "5, 3. ja 4. krs", {}, {"street": "Tie", "housenumber": "5"}, ("extras.addr:floor",)),
    ("Toinen linja", "", {}, {}, ("extras.addr:floor",)),
    (
        "Viides linja",
        "9, 2. krs",
        {},
        {"street": "Viides linja", "housenumber": "9", "extras.addr:floor": "2"},
        (),
    ),
    (
        "Katu",
        "13, katutaso",
        {},
        {"street": "Katu", "housenumber": "13"},
        ("extras.addr:floor", "extras.level"),
    ),
    ("Talholmen virkistysalue", "", {}, {"extras.addr:place": "Talholmen virkistysalue"}, ("street_address",)),
    ("Saaristonkatu", "", {}, {"street": "Saaristonkatu"}, ("street_address",)),
    ("Didrichsenin taidemuseo, Kuusilahdenkuja", "1", {}, {"street": "Kuusilahdenkuja", "housenumber": "1"}, ()),
    (
        "Kielotie",
        "42 asunnot 1-4",
        {"postcode": "01300", "office": "VANTAA"},
        {"street": "Kielotie", "housenumber": "42", "extras.addr:unit": "asunnot 1-4"},
        (),
    ),
    (
        "Oikopolku",
        "2 as 3",
        {},
        {"street": "Oikopolku", "housenumber": "2", "extras.addr:unit": "as 3"},
        ("street_address",),
    ),
    ("Katu", "51, 51", {}, {"street": "Katu", "housenumber": "51"}, ("street_address", "extras.addr:unit")),
    ("Juurikoskenkatu", "1 lt 7", {}, {"street": "Juurikoskenkatu", "housenumber": "7"}, ()),
    ("Ulkofantintie", "", {}, {"street": "Ulkofantintie"}, ()),
    ("Luolavuorenpolku", "", {}, {"street": "Luolavuorenpolku"}, ()),
    ("Örninkatu", "15 ovi 28", {}, {"housenumber": "15", "extras.addr:unit": "ovi 28"}, ()),
    ("Kummelivuorentie", "2 ja 4", {}, {"housenumber": "2", "extras.addr:unit": "4"}, ()),
    ("Muurlantie", "365 E as 5", {}, {"housenumber": "365", "extras.addr:unit": "E as 5"}, ()),
    ("Sampsantie", "17a (Metsolantie 18, Peller", {}, {"housenumber": "17a"}, ()),
    ("Päiväkodintie", "4 a 7-8", {}, {"housenumber": "4", "extras.addr:unit": "a 7-8"}, ()),
    (
        "Tikkamäentie 16",
        "talo 7, 7 krs.",
        {},
        {"housenumber": "16", "extras.addr:unit": "talo 7", "extras.addr:floor": "7"},
        (),
    ),
    (
        "Kauppakuja 2 A 1",
        "2 A 1",
        {},
        {"street": "Kauppakuja", "housenumber": "2", "extras.addr:unit": "A 1"},
        (),
    ),
    (
        "Pappilantie 11, pielavesi",
        "",
        {"office": "PIELAVESI"},
        {"street": "Pappilantie", "housenumber": "11"},
        (),
    ),
    ("Tahtimarssi 3", "Oulu", {"office": "OULU"}, {"street": "Tahtimarssi", "housenumber": "3"}, ()),
    ("Kalevalantie 13", "90570", {}, {"street": "Kalevalantie", "housenumber": "13"}, ()),
    ("Tie", "PL 24", {}, {"housenumber": None}, ()),
    ("Tie", "15 rak.1 B-rappu", {}, {"housenumber": "15", "extras.addr:unit": "rak.1 B-rappu"}, ()),
    ("Tivolikuja", "1 Alppiharju", {}, {"street": "Tivolikuja", "housenumber": "1"}, ()),
    (
        "Mannerheimintie / Runeberginkatu",
        "12 A 1",
        {},
        {"addr_full": "Mannerheimintie / Runeberginkatu", "extras.addr:unit": "A 1"},
        (),
    ),
    ("Katu", "12/14", {}, {"housenumber": "12-14"}, ()),
    ("Tie", "10 11111", {"postcode": ""}, {"housenumber": "10"}, ("extras.addr:unit",)),
    ("Pasilan asema", "", {}, {"addr_full": "Pasilan asema"}, ("extras.addr:place",)),
    (
        "Varastotie 4",
        "67100",
        {"postcode": "67100", "office": "KOKKOLA"},
        {"street": "Varastotie"},
        ("extras.addr:unit",),
    ),
    ("Pl 52", "", {"postcode": "20520", "office": "TURKU"}, {"postcode": "20520"}, ("street", "housenumber")),
]


@pytest.mark.parametrize("road,number,kw,want,absent", _ADDR_CASES)
def test_address(road, number, kw, want, absent):
    check_addr(road, number, want=want, absent=absent, **kw)


def test_route_descriptions_stay_freeform():
    # Numberless route descriptions carry the name with no number.
    for road in (
        "Metsäautotie välillä Lapinlahdentie 1175 - Pitkämäentie 641",
        "Metsäautotie välilla Lapinlahdentie 1175 - Pitkämäentie 641",
    ):
        item = addressed(make_spider(), road, "")
        assert item.get("housenumber") is None
        assert item["addr_full"] == road


def test_postcode_tail_stripped_from_number():
    assert make_spider()._resolve_number_tail("03100 Nummela") is None
    assert make_spider()._resolve_number_tail("2 vån") is None


def test_stair_range_units_parse():
    # Kauppakatu 27b A2-4: staircase-letter + apartment-range tails parse
    # to housenumber + unit, not freeform.
    assert make_spider()._split_addr_tokens("Kauppakatu 27b A2-4".split()) == ("Kauppakatu", "27b", "A2-4")


# ---- Categories: health ----------------------------------------------------------
C = Categories

_HEALTH_CASES = [
    # Precedence: police/social/dental outrank on-call; plain stays urgent.
    ("Rauman poliisiasema, poliisipäivystys", C.POLICE, _SKIP),
    ("Sosiaali- ja kriisipäivystys", C.SOCIAL_FACILITY, _SKIP),
    ("Päivystys", C.CLINIC_URGENT, _SKIP),
    ("Forssan hammashoidon arkipäivystys", C.DENTIST, _SKIP),
    ("Seminaarikoulun hammashoitola", C.DENTIST, _SKIP),
    ("Kuopion Canthia, suun perusterveydenhuolto", C.DENTIST, _SKIP),
    ("Pirkanmaan suun erikoishoidon yksikkö - oikomishoito", C.DENTIST, _SKIP),
    # School-hosted health files as health; nurse-led carries the extra.
    ("Opiskeluhuolto", C.CLINIC, {"healthcare": "nurse"}),
    ("Kouluterveydenhuolto", C.CLINIC, _SKIP),
    ("Pihlajamäen neuvola", C.CLINIC, _SKIP),
    ("Esiopetuksen opiskeluhuolto, Laurentius-päiväkoti", C.CLINIC, {"healthcare": "nurse"}),
    ("Esiopetuksen opiskeluhuolto, Kantvikin päiväkoti", C.CLINIC, {"healthcare": "nurse"}),
    ("Opiskeluhuolto, Karis svenska högstadium", C.CLINIC, {"healthcare": "nurse"}),
    ("Merilahden peruskoulu, Jaluspolun toimipiste, kouluterveydenhuolto", C.CLINIC, _SKIP),
    # Wards, receptions, therapy units.
    ("Malmin osasto 13", C.CLINIC, _SKIP),
    ("Laakson osasto 3", C.CLINIC, _SKIP),
    ("Suursuon osasto 23", C.CLINIC, _SKIP),
    ("Laakson vuodeosasto 13 (infektio-osasto)", C.CLINIC, _SKIP),
    ("Pellon vuodeosasto", C.CLINIC, _SKIP),
    ("Geriatrinen akuuttiosasto", C.CLINIC, _SKIP),
    ("Terveysaseman vastaanotto", C.CLINIC, _SKIP),
    ("Akaan lääkärin ja hoitajan vastaanotot", C.CLINIC, _SKIP),
    ("Kuntoutuksen poliklinikat", C.CLINIC, _SKIP),
    ("Mielialahäiriötyöryhmä, Tyks, Raisio", C.CLINIC, _SKIP),
    ("Diabeteskeskus", C.CLINIC, _SKIP),
    ("Maahanmuuttajien terveyspalvelut", C.CLINIC, _SKIP),
    ("Fysioterapia Kankaanpää", C.CLINIC, {"healthcare": "physiotherapist"}),
    ("Oriveden puheterapian vastaanotot", C.CLINIC, {"healthcare": "speech_therapist"}),
    ("Teerijärven hyvinvointiasema, fysioterapia", _SKIP, {"healthcare": "physiotherapist"}),
    ("Diabeteshoitaja, Kaarina", _SKIP, {"healthcare": "nurse"}),
    ("Jalkaterapeutti, Loimaa", C.CLINIC, {"healthcare": "podiatrist"}),
    ("Varhaiskasvatuksen puheterapeutti", C.CLINIC, _SKIP),
    ("Koulupsykologi", C.CLINIC, _SKIP),
    ("Oikeuspsykiatrian vastaanotto, Auroran sairaala", C.CLINIC, _SKIP),
    ("Lasten ja nuorten oikeuspsykologian yksikkö", C.CLINIC, _SKIP),
    ("Opioidiriippuvaisten korvaushoito", C.CLINIC, _SKIP),
    ("Päihdevieroitus", C.CLINIC, _SKIP),
    ("Leikkaus ja anestesia", C.CLINIC, _SKIP),
    ("Leikkaushoitokeskus", C.CLINIC, _SKIP),
    ("Sisätaudit", C.CLINIC, _SKIP),
    ("Silmätautien hoito", C.CLINIC, _SKIP),
    ("Syöpätaudit ja sädehoito", C.CLINIC, _SKIP),
    ("Syöpätautien ja verisairauksien sairaansijat", C.CLINIC, _SKIP),
    ("Munuaisyksikkö", C.CLINIC, _SKIP),
    ("Tähystys", C.CLINIC, _SKIP),
    ("Dialyysi- ja munuaisyksikkö", C.CLINIC, _SKIP),
    ("Neulanvaihtopiste", C.CLINIC, _SKIP),
    ("Tartuntataudit", C.CLINIC, _SKIP),
    ("Vatsakeskus, Tays Hatanpää", C.CLINIC, _SKIP),
    ("Vaativa kuntoutusyksikkö, Tays Hatanpää", C.CLINIC, _SKIP),
    ("Arviointiyksikkö", C.CLINIC, _SKIP),
    ("Katriinan sairaalan röntgen", C.CLINIC, {"healthcare": "medical_imaging"}),
    ("Rontgen Pori", C.CLINIC, {"healthcare": "medical_imaging"}),
    ("Kiskon äitiys- ja lastenneuvola", _SKIP, {"healthcare:speciality": "maternal_and_child_health"}),
    ("Lapin keskussairaalan laboratorio", C.CLINIC, {"healthcare": "laboratory"}),
    ("Sevettijärven terveystalo", C.CLINIC, _SKIP),
    ("Kliininen neurofysiologia, Porvoon sairaala", C.CLINIC, _SKIP),
    ("Hyrynsalmen muistineuvola", C.CLINIC, None),
    ("Raision Muistikeskus", C.CLINIC, _SKIP),
    ("Kohdunkaulan syövän seulonta", C.CLINIC, _SKIP),
    ("Sikiöseulonnat", C.CLINIC, _SKIP),
    ("Sikiötutkimusyksikkö", C.CLINIC, _SKIP),
    ("Tutkimusyksiköt, toimipisteet", C.CLINIC, _SKIP),
    ("Rintasyöpäseulonta Oulun yliopistollisessa sairaalassa", C.CLINIC, _SKIP),
    ("Terveys- ja hyvinvointikeskus", C.CLINIC, _SKIP),
    ("Terveyskeskus Mehiläinen Espoontori", C.CLINIC, _SKIP),
    ("Vesilahden lähiasema", C.CLINIC, _SKIP),
    ("Selviämishoitoasema", C.CLINIC, _SKIP),
    ("Selviämisasema", C.CLINIC, _SKIP),
    ("Sydänasema", C.CLINIC, _SKIP),
    ("Sydänyksikkö", C.CLINIC, _SKIP),
    ("Sydänosasto", C.CLINIC, _SKIP),
    ("Syömishäiriötiimi Verso", C.CLINIC, _SKIP),
    ("Ravitsemusterapia, Kustavi, Laitila", C.CLINIC, _SKIP),
    ("Terveyskeskusryhmä", C.CLINIC, _SKIP),
    ("Neuvonta terveysasemalla", C.CLINIC, _SKIP),
    ("Nuorisoasema mielenterveystyö", C.CLINIC, _SKIP),
    ("Nuorisopsykiatrian poliklinikka", C.CLINIC, _SKIP),
    ("Konneveden, Uuraisten ja Äänekosken nuorten mielenterveys- ja päihdetyön tiimi", C.CLINIC, _SKIP),
    ("Nuorten päihdepalvelu Pysäkki", C.CLINIC, _SKIP),
    ("Lasten ja nuorten mielenterveyspalvelut", C.CLINIC, _SKIP),
    ("Nuorten sukupuoli-identiteetin tutkimusvastaanotto, Pasila", C.CLINIC, _SKIP),
    ("Terveyspalvelut", C.CLINIC, _SKIP),
    # Hospitals (subunits downgrade to clinic).
    ("Satasairaala", C.HOSPITAL, _SKIP),
    ("Kymenlaakson psykiatrinen sairaala", C.HOSPITAL, _SKIP),
    ("Palliatiivinen yksikkö, Sastamalan sairaala", C.CLINIC, _SKIP),
    ("Päiväsairaala", C.CLINIC, _SKIP),
    # Pharmacies and medical-supply shops.
    ("Apoteket", C.PHARMACY, _SKIP),
    ("Kirjavantolpan apteekki", C.PHARMACY, _SKIP),
    ("Kotkan 5. Karhulan Tori apteekki", C.PHARMACY, _SKIP),
    ("Hämeenlinnan I Tori-apteekki", C.PHARMACY, _SKIP),
    ("CPAP-tarvikejakelu", C.SHOP_MEDICAL_SUPPLY, _SKIP),
    ("Hoitotarvikejakelu", C.SHOP_MEDICAL_SUPPLY, _SKIP),
    # Vets (municipal vet branches keep vet over supervision).
    ("Eläinlääkäri Eura", C.VETERINARY, _SKIP),
    ("Eläinhoitola", C.VETERINARY, _SKIP),
    ("Heinolan Lintuhoitola", C.VETERINARY, _SKIP),
    ("Päijät-Hämeen ympäristöterveys, Orimattilan kunnaneläinlääkärin toimipiste", C.VETERINARY, _SKIP),
    ("Veikkolan näytteenoton lähipalvelu", C.SAMPLE_COLLECTION, _SKIP),
    # No-enum rows stay generic.
    ("Vainajansäilytys, Ahveniston sairaala", None, None),
    ("Helsingin vainajatilat", None, None),
]


@pytest.mark.parametrize("fi,want_cat,want_extra", _HEALTH_CASES)
def test_category_health(fi, want_cat, want_extra):
    check_cat(fi, want_cat, want_extra)


# ---- Categories: education -----------------------------------------------------

_EDU_CASES = [
    ("Kouluravintola, Pihlajamäen ala-asteen koulu", C.CANTEEN, _SKIP),
    ("Kouluravintola, Pukinmäenkaaren peruskoulu", C.CANTEEN, _SKIP),
    ("Koskelan monipuolinen palvelukeskus / Hoitoalan ruokapalvelut", C.CANTEEN, _SKIP),
    ("Keuda Kerava", C.COLLEGE, _SKIP),
    ("Koulutuskeskus Salpaus", C.COLLEGE, _SKIP),
    ("Kansalaisopisto", C.COLLEGE, _SKIP),
    ("Sipoon opisto / Opintien palvelupiste ja liikuntatila", C.COLLEGE, _SKIP),
    ("Koulutalo", C.SCHOOL, _SKIP),
    ("Helsingin yhteislyseo", C.SCHOOL, _SKIP),
    ("Myllytullin koulu", C.SCHOOL, _SKIP),
    ("Tiernan koulu, Heinätori", C.SCHOOL, _SKIP),
    ("Koulun piha", C.SCHOOL, _SKIP),
    ("Urheilupuiston koulu", C.SCHOOL, _SKIP),
    ("Kuvataidekoulu", C.SCHOOL, _SKIP),
    ("Nordsjö lågstadieskola", C.SCHOOL, _SKIP),
    ("Gymnasium", C.SCHOOL, _SKIP),
    ("Gymnasiet i Petalax", C.SCHOOL, _SKIP),
    ("Koulukuraattori", C.SCHOOL, _SKIP),
    ("Soveltava temppuilu kouluikäisille", None, _SKIP),
    ("Happy Toddlers", C.KINDERGARTEN, _SKIP),
    ("Daycare Daisy Oy", C.KINDERGARTEN, _SKIP),
    ("Sammontalon päiväkodin Uus-Lavolan toimintayksikkö", C.KINDERGARTEN, _SKIP),
    ("Pääskyvuoren leikkikerho", C.KINDERGARTEN, _SKIP),
    ("Leikkikoulu", C.KINDERGARTEN, _SKIP),
    ("Urheiluleikkikerho Kanervat", C.KINDERGARTEN, _SKIP),
    ("Päiväkotiryhmä Vekkula", C.KINDERGARTEN, _SKIP),
    ("Alhaisten koulun esiopetusryhmä", C.KINDERGARTEN, _SKIP),
    ("Kämmenniemen päiväkoti Terälahden lisäryhmä", C.KINDERGARTEN, _SKIP),
    ("Päiväkodin vuorohoitoryhmä", C.KINDERGARTEN, _SKIP),
    ("Perhepäivähoitaja Tiia Ruotsalainen", C.KINDERGARTEN, _SKIP),
    ("Espoon keskuksen yksityisen hoidon tuen päiväkodit", C.KINDERGARTEN, _SKIP),
    ("Prästgårdsbackens förskola, Gesterby", C.KINDERGARTEN, _SKIP),
    ("Kyrkoby förskola", C.KINDERGARTEN, _SKIP),
    ("Söderkulla förskola", C.KINDERGARTEN, _SKIP),
    ("Södra familjedagvårdsområden", C.KINDERGARTEN, _SKIP),
    ("Ryhmäperhepäivähoitokoti Rastas", C.KINDERGARTEN, _SKIP),
    ("Luomupäiväkoti Kirsikka Laajasalo", C.KINDERGARTEN, _SKIP),
    ("Päiväkoti Vihtori", C.KINDERGARTEN, _SKIP),
    ("Pilke Kilonkallio", C.KINDERGARTEN, _SKIP),
    ("Päiväkoti Ankkalampi Duckies, Herttoniemenranta", C.KINDERGARTEN, _SKIP),
    ("Norlandia Kärry", C.KINDERGARTEN, _SKIP),
    ("Iltapäivätoiminta / Aurinkolahden peruskoulu", C.COMMUNITY_CENTRE, _SKIP),
    (
        "Kuparivuoren aamu- ja iltapäivätoiminta sekä iltapäivätoiminnan pienryhmä",
        C.COMMUNITY_CENTRE,
        _SKIP,
    ),
    ("Iltapäivätoiminta / Puotilan ala-aste, Saalem-Nuoret ry", C.COMMUNITY_CENTRE, _SKIP),
    ("Koulumuseo Lagstad", C.MUSEUM, _SKIP),
    ("Saukkojärven kotiseutu- ja koulumuseo", C.MUSEUM, _SKIP),
    ("Apteekkimuseo", C.MUSEUM, _SKIP),
    ("Apteekkimuseo ja Qwenselin talo", C.MUSEUM, _SKIP),
    ("Huvilamuseo Villa Rulludd", C.MUSEUM, _SKIP),
    ("Sairaalamuseo", C.MUSEUM, _SKIP),
    ("Näyttelyhalli", C.MUSEUM, _SKIP),
    ("Näyttelykeskus WeeGee", C.MUSEUM, _SKIP),
    ("Leo Torpan kamerakokoelma", C.MUSEUM, _SKIP),
    ("Sonkajärven kirjaston näyttelysali", C.MUSEUM, _SKIP),
    ("Valkeakosken kaupunginkirjaston lehtisali", C.LIBRARY, _SKIP),
    ("Lehtilukusali", C.LIBRARY, _SKIP),
    ("Lehtisali ja omatoimikirjasto", C.LIBRARY, _SKIP),
    ("Dagsmarkin lainausasema", C.LIBRARY, _SKIP),
    ("Aikuiskoulutus", C.OFFICE_GOVERNMENT, _SKIP),
    ("Koulutukset ja luennot", C.OFFICE_GOVERNMENT, _SKIP),
    ("Kasvatuksen ja koulutuksen toimiala, hallinto", C.OFFICE_GOVERNMENT, _SKIP),
    ("Vesilahden koulutoimisto", C.OFFICE_GOVERNMENT, _SKIP),
    ("Koulutoimisto", C.OFFICE_GOVERNMENT, _SKIP),
    ("Perusopetus", C.OFFICE_GOVERNMENT, _SKIP),
]


@pytest.mark.parametrize("fi,want_cat,want_extra", _EDU_CASES)
def test_category_education(fi, want_cat, want_extra):
    check_cat(fi, want_cat, want_extra)


def test_koululainen_pupils_are_not_schools():
    assert cat(make_spider(), "Koululaisen aamu- ja iltapäivätoiminta")[0] != Categories.SCHOOL


# ---- Categories: social housing and care -------------------------------------------
C = Categories

_SOCIAL_CASES = [
    # Group homes house; bare desks don't.
    ("Ryhmäkoti Karkkula", C.SOCIAL_FACILITY, {"social_facility": "group_home"}),
    ("Outamon lastenkoti Noko", C.SOCIAL_FACILITY, {"social_facility": "group_home"}),
    ("Ryhmäkoti Sinfonia", C.SOCIAL_FACILITY, {"social_facility": "group_home"}),
    ("Hakalan ryhmäkodit", C.SOCIAL_FACILITY, {"social_facility": "group_home"}),
    ("Asumispalveluyksikkö Virrankoti", _SKIP, {"social_facility": "group_home"}),
    ("Töölön seniorikeskus/Helmi ryhmäkoti", C.SOCIAL_FACILITY, {"social_facility": "group_home"}),
    ("Nuorten vastaanottokoti Havurinne", C.SOCIAL_FACILITY, {"social_facility": "group_home"}),
    ("Uudenkoiviston vastaanottokoti", C.SOCIAL_FACILITY, {"social_facility": "group_home"}),
    ("Rovaniemen Etelärinteen lapsi- ja nuorisokoti", _SKIP, {"social_facility": "group_home"}),
    ("Eskolakoti 1 ja 2", C.SOCIAL_FACILITY, _SKIP),
    ("Lastensuojelulaitos", C.SOCIAL_FACILITY, _SKIP),
    ("Mielenterveys- ja päihdekuntoutujien asumispalveluyksiköt Tähkä ja Jyvä", C.SOCIAL_FACILITY, _SKIP),
    ("Lastensuojelun ja perhesosiaalityön vertaisryhmätoiminta", C.SOCIAL_FACILITY, _SKIP),
    # Nursing needs housing evidence.
    ("Palvelukoti Osmanrinne", C.NURSING_HOME, _SKIP),
    ("Ikäihmisten tehostettu palveluasuminen", C.NURSING_HOME, _SKIP),
    ("Ympärivuorokautinen palveluasuminen", C.NURSING_HOME, _SKIP),
    ("Koskelan palveluasumisyksikkö", C.NURSING_HOME, _SKIP),
    ("Linnavuoren palvelukodit", C.NURSING_HOME, _SKIP),
    ("Hoitokoti Toppila", C.NURSING_HOME, _SKIP),
    ("Hoitokoti, Hyrynsalmen hoitokoti", C.NURSING_HOME, _SKIP),
    ("Ruusukujan palveluasunnot", C.NURSING_HOME, _SKIP),
    ("Lyhytaikaisyksikkö Selvari, Seinäjoki", C.NURSING_HOME, _SKIP),
    ("Oulun lyhytaikaishoidon yksikkö Elviira", C.NURSING_HOME, _SKIP),
    ("Esperi Hoivakoti Vihtori", C.NURSING_HOME, _SKIP),
    ("Iin palvelukoti Emmintupa", C.NURSING_HOME, _SKIP),
    ("Palvelukoti Snällintupa", C.NURSING_HOME, _SKIP),
    # Supported housing assists; assessments never house.
    ("Matinniitty tuettu asuminen", C.ASSISTED_LIVING, _SKIP),
    ("Mielenterveyskuntoutujien tuettu asuminen", C.ASSISTED_LIVING, _SKIP),
    ("Roihuvuoren tukiasunnot", C.ASSISTED_LIVING, _SKIP),
    # Shelters shelter; desks stay desks.
    ("Ensikotitoiminta", C.SHELTER, _SKIP),
    ("Hätämajoitusyksikkö Viisikko", C.SHELTER, _SKIP),
    ("Mikkelin turvakoti", C.SOCIAL_FACILITY, {"social_facility": "shelter"}),
    ("Turvakoti palvelupiste", C.OFFICE_GOVERNMENT, _SKIP),
    # Social-facility services.
    ("Kuntoutusohjaus- ja asiantuntijapalvelut", C.SOCIAL_FACILITY, _SKIP),
    ("Vaativat kehitysvammapalvelut", C.SOCIAL_FACILITY, _SKIP),
    ("Perhetukikeskus Päiväperho", C.SOCIAL_FACILITY, _SKIP),
    ("Seri-tukikeskus", C.SOCIAL_FACILITY, _SKIP),
    ("Hävikkiruoan jako työttömille ja vähävaraisille", C.SOCIAL_FACILITY, _SKIP),
    ("Hävikkiruokajakelu", C.SOCIAL_FACILITY, _SKIP),
    ("Yhteisen pöydän hävikkiterminaali", C.SOCIAL_FACILITY, _SKIP),
    ("Ruoka-apua (leipää)", C.SOCIAL_FACILITY, _SKIP),
    ("Ruokajako", C.SOCIAL_FACILITY, _SKIP),
    ("Naulakko - vaate- ja tavara-apu", C.SOCIAL_FACILITY, _SKIP),
    ("Turun kulttuuripaja Casa", C.SOCIAL_FACILITY, _SKIP),
    ("Lohjan päiväaikainen toiminta", C.SOCIAL_FACILITY, _SKIP),
    ("Asumispalvelut kehitysvammaisille lapsille", C.SOCIAL_FACILITY, _SKIP),
    ("Kauklahden asumispalvelut", C.SOCIAL_FACILITY, _SKIP),
    # Care homes on Puistikko road stay homes, never parks.
    ("Onnikoti Puistikkotie", C.SOCIAL_FACILITY, None),
    ("Kotihoito Lappeenranta Läntinen", C.SOCIAL_FACILITY, _SKIP),
    ("Kotihoito/Töölö 2 lähipalvelualue", C.SOCIAL_FACILITY, _SKIP),
    ("Kotihoito/Pitäjänmäki 1 lähipalvelualue", C.SOCIAL_FACILITY, _SKIP),
    ("Oulun Limingantulli-Meritulli kotihoito", C.SOCIAL_FACILITY, _SKIP),
    ("Perheasiain neuvottelukeskus", C.SOCIAL_FACILITY, _SKIP),
    ("Suomenkielinen seniorikerho", C.SOCIAL_FACILITY, _SKIP),
    ("Seniorikerho", C.SOCIAL_FACILITY, _SKIP),
    ("Seniori-info", C.SOCIAL_FACILITY, _SKIP),
    ("Ikäihmisten päivätoiminta, Kihniö", C.SOCIAL_FACILITY, _SKIP),
    ("Rovaniemen päiväkeskus Veitikantupa", C.SOCIAL_FACILITY, _SKIP),
    ("Pirkkalan sote-aseman lähitori", C.SOCIAL_FACILITY, _SKIP),
    ("Messukylän lähitori, Tampere", C.SOCIAL_FACILITY, _SKIP),
    ("Innopaja & Kädentaitokeskus", C.SOCIAL_FACILITY, {"social_facility": "workshop"}),
    ("Kädentaitopaja", _SKIP, {"social_facility": "workshop"}),
    ("Miehikkälän työpaja", _SKIP, {"social_facility": "workshop"}),
    ("Palvelut ikäihmisille", C.OFFICE_GOVERNMENT, _SKIP),
    ("Ikäihmisten palvelujen hakemukset", C.OFFICE_GOVERNMENT, _SKIP),
    (
        "Ikifit Oy, hyvinvointikoti Jukola/Hannes, Hämeenlinna, yhteisöllisen asumisen ostopalvelut",
        C.SOCIAL_FACILITY,
        _SKIP,
    ),
]


@pytest.mark.parametrize("fi,want_cat,want_extra", _SOCIAL_CASES)
def test_category_social(fi, want_cat, want_extra):
    check_cat(fi, want_cat, want_extra)


# ---- Categories: civic offices, courts, companies --------------------------------

_CIVIC_CASES = [
    ("Apuvälinepalvelu", C.OFFICE_GOVERNMENT, _SKIP),
    ("Mittauspalvelut", C.OFFICE_GOVERNMENT, _SKIP),
    ("Sisäinen tarkastus", C.OFFICE_GOVERNMENT, _SKIP),
    ("Työllistymistä edistävä monialainen palvelu TYM", C.OFFICE_GOVERNMENT, _SKIP),
    ("Iisalmen poliisiasema", C.POLICE, _SKIP),
    ("Poliisiasema", C.POLICE, _SKIP),
    ("Keski-Uudenmaan ympäristökeskus", C.OFFICE_GOVERNMENT, _SKIP),
    ("Kaupunkikehitys -toimiala", C.OFFICE_GOVERNMENT, _SKIP),
    ("Terveysvalvonta", C.OFFICE_GOVERNMENT, _SKIP),
    ("Kalajoen kaupungin ympäristövalvonta", C.OFFICE_GOVERNMENT, _SKIP),
    ("Elintarviketurvallisuusyksikkö", C.OFFICE_GOVERNMENT, _SKIP),
    ("Ympäristöterveyspalvelut, Paraisten toimipiste", C.OFFICE_GOVERNMENT, _SKIP),
    ("Ympäristönsuojelu- ja ympäristöterveyspalveluiden Iisalmen toimipiste", C.OFFICE_GOVERNMENT, _SKIP),
    ("Lentotulli", C.OFFICE_GOVERNMENT, _SKIP),
    ("Nuorisoasema", C.OFFICE_GOVERNMENT, _SKIP),
    ("Nuorisoasema Klaara", C.OFFICE_GOVERNMENT, _SKIP),
    ("Nuorisotoimisto", C.OFFICE_GOVERNMENT, _SKIP),
    ("Nuorisopalvelujen asiakaspalvelu", C.OFFICE_GOVERNMENT, _SKIP),
    ("Nuorisovaltuusto", C.OFFICE_GOVERNMENT, _SKIP),
    ("Helsingin keskusvaalilautakunta", C.OFFICE_GOVERNMENT, _SKIP),
    ("Helsingin kaupunginvaltuusto", C.OFFICE_GOVERNMENT, _SKIP),
    ("Hankinnat ja Kilpailuttaminen", C.OFFICE_GOVERNMENT, _SKIP),
    ("Tonttijako", C.OFFICE_GOVERNMENT, _SKIP),
    ("Maakuntatalo", C.OFFICE_GOVERNMENT, _SKIP),
    ("Welcome Office", C.OFFICE_GOVERNMENT, _SKIP),
    ("Lastensuojelu", C.OFFICE_GOVERNMENT, _SKIP),
    ("Oriveden kaupungin asumispalvelut", C.OFFICE_GOVERNMENT, _SKIP),
    ("Maankäyttö- ja asumispalvelut", C.OFFICE_GOVERNMENT, _SKIP),
    ("Henkilöstöosasto", C.OFFICE_GOVERNMENT, _SKIP),
    ("Joroisten kunnan elinkeinotoimi", C.OFFICE_GOVERNMENT, _SKIP),
    ("Vihdin kunnan kulttuuri- ja vapaa-aika", C.OFFICE_GOVERNMENT, _SKIP),
    ("Työllisyyskoordinaattori", C.OFFICE_GOVERNMENT, _SKIP),
    ("Maaseutupalvelut", C.OFFICE_GOVERNMENT, _SKIP),
    ("Maaseutupalvelut, Rovaniemen toimipiste", C.OFFICE_GOVERNMENT, _SKIP),
    ("Museoiden toimisto", C.OFFICE_GOVERNMENT, _SKIP),
    ("Yläjärven talousneuvola", C.OFFICE_GOVERNMENT, _SKIP),
    ("Potilasasiavastaava", C.OFFICE_GOVERNMENT, _SKIP),
    ("Potilasasiamiehen asiointipaikka, Forssan sairaala", C.OFFICE_GOVERNMENT, _SKIP),
    ("Rikosuhripäivystyksen Keski-Pohjanmaan palvelupiste", C.OFFICE_GOVERNMENT, _SKIP),
    ("Luustoinfo osteoporoosia sairastaville / Lahti", C.OFFICE_GOVERNMENT, _SKIP),
    ("Yhteispalvelu Vaasa - Kansalaisinfo", C.OFFICE_GOVERNMENT, _SKIP),
    ("Stadshus", C.OFFICE_GOVERNMENT, _SKIP),
    ("Kaupunkitila- ja maisemasuunnittelu", C.OFFICE_GOVERNMENT, _SKIP),
    ("Kuulolähipalvelu", C.OFFICE_GOVERNMENT, _SKIP),
    ("OLKA-pisteiltä tietoa yhdistysten toiminnasta", C.OFFICE_GOVERNMENT, _SKIP),
    ("Elinkeinopalvelut", C.OFFICE_GOVERNMENT, _SKIP),
    ("Asiakaspalvelupiste Tietotupa", C.OFFICE_GOVERNMENT, _SKIP),
    ("BusinessAsema", C.OFFICE_GOVERNMENT, _SKIP),
    ("Asemakaavoitus", C.OFFICE_GOVERNMENT, _SKIP),
    ("Kokkolan aluekeskusrekisteri", C.OFFICE_GOVERNMENT, _SKIP),
    ("Espoon aluekeskusrekisteri", C.OFFICE_GOVERNMENT, _SKIP),
    ("Lappeenrannan toimipiste, Koulukatu 14", C.OFFICE_GOVERNMENT, _SKIP),
    ("Pargas serviceenhet", C.OFFICE_GOVERNMENT, _SKIP),
    ("Kaarinan kaupungin rakennusvalvonnan lupa-asiat", C.OFFICE_GOVERNMENT, _SKIP),
    ("Eläinsuojelu", C.OFFICE_GOVERNMENT, _SKIP),
    ("Vauvaperheryhmä Untuva toimipiste", C.OFFICE_GOVERNMENT, _SKIP),
    ("Mänttä-Vilppulan lapsiperheiden sosiaalipalvelujen vastaanotot", C.OFFICE_GOVERNMENT, _SKIP),
    ("Kaupunginosan toimisto", C.OFFICE_GOVERNMENT, _SKIP),
    ("Maaseutupalvelut", C.OFFICE_GOVERNMENT, _SKIP),
    ("Haapajärven päihdepalvelujen toimipiste", C.CLINIC, _SKIP),
    ("Asiakaspalvelupisteet Helsinki-Vantaan lentoasemalla", C.OFFICE_GOVERNMENT, _SKIP),
    ("Omnian Palvelutori", C.OFFICE_GOVERNMENT, _SKIP),
    ("Maahanmuuttajien ohjaus- ja palvelupiste Navigaattori", C.OFFICE_GOVERNMENT, None),
    ("Klubitalo Roihulan asiakaspalvelu", C.OFFICE_GOVERNMENT, _SKIP),
    ("Raatihuone", C.OFFICE_GOVERNMENT, _SKIP),
    ("Käräjäoikeus", C.COURTHOUSE, _SKIP),
    ("Käräjäsali", C.COURTHOUSE, _SKIP),
    ("Oulun käräjäoikeus, Ruskonselän istuntosali", C.COURTHOUSE, _SKIP),
    ("Oulun käräjäoikeus, Ylivieskan kanslia", C.COURTHOUSE, _SKIP),
    ("Vakuutusoikeus", C.COURTHOUSE, _SKIP),
    ("Korkein oikeus", C.COURTHOUSE, _SKIP),
    ("Helsingin hallinto-oikeus", C.COURTHOUSE, _SKIP),
    ("Hovioikeus", C.COURTHOUSE, _SKIP),
    ("Mikkelin Asumisoikeus Oy:n toimisto", C.OFFICE_COMPANY, _SKIP),
    ("Helsingin Asumisoikeus Oy", C.OFFICE_COMPANY, _SKIP),
    ("Imatran Seudun Kehitysyhtiö Oy", C.OFFICE_COMPANY, _SKIP),
    ("Ylämyllyn yritystalot", C.OFFICE_COMPANY, _SKIP),
    ("Kiinteistö Oy Keskiväli", C.OFFICE_COMPANY, _SKIP),
    ("Messilän Pääkonttori", C.OFFICE_COMPANY, _SKIP),
    ("Kajaanin Vesi -liikelaitos", C.OFFICE_COMPANY, _SKIP),
    ("Pirkanmaan oikeusaputoimisto", C.OFFICE_LAWYER, _SKIP),
]


@pytest.mark.parametrize("fi,want_cat,want_extra", _CIVIC_CASES)
def test_category_civic(fi, want_cat, want_extra):
    check_cat(fi, want_cat, want_extra)


# ---- Categories: community venues --------------------------------------------------

_COMMUNITY_CASES = [
    ("Kerhotalo", C.COMMUNITY_CENTRE, _SKIP),
    ("Omaisten vertaistukiryhmä", C.COMMUNITY_CENTRE, _SKIP),
    ("Omaistaan hoitavien vertaisryhmät", C.COMMUNITY_CENTRE, _SKIP),
    ("Vertaistukiryhmä syöpään sairastuneille", C.COMMUNITY_CENTRE, _SKIP),
    ("Imatran Sydänkerho", C.COMMUNITY_CENTRE, _SKIP),
    ("Hervannan vapaa-aikakeskus", C.COMMUNITY_CENTRE, _SKIP),
    ("Karvetin klubitalo", C.COMMUNITY_CENTRE, _SKIP),
    ("Stadin yhteisötalo Alppila", C.COMMUNITY_CENTRE, _SKIP),
    ("Hyvinvointi- ja harrastuskeskus", C.COMMUNITY_CENTRE, _SKIP),
    ("Hervannan yhteisökeskus", C.COMMUNITY_CENTRE, _SKIP),
    ("Kulttuuritila Näkkäri", C.COMMUNITY_CENTRE, _SKIP),
    ("Etappi yhteisötila", C.COMMUNITY_CENTRE, _SKIP),
    ("Joutsenon kirjaston monitoimitila Olkkari", C.COMMUNITY_CENTRE, _SKIP),
    ("Kumppanuustalo Artteli", C.COMMUNITY_CENTRE, _SKIP),
    ("Järjestötalon aukioloaika", C.COMMUNITY_CENTRE, _SKIP),
    ("Vartsalan työväentalo", C.COMMUNITY_CENTRE, _SKIP),
    ("Toimintapäivät Lohjan Työväentalolla", C.COMMUNITY_CENTRE, _SKIP),
    ("Sonkajärven kotiseututalo", C.COMMUNITY_CENTRE, _SKIP),
    ("Kirkonkylän kylätalo", C.COMMUNITY_CENTRE, _SKIP),
    ("Pohjanmaan Yhdistykset ry", C.COMMUNITY_CENTRE, _SKIP),
    ("Mielenterveyskuntoutujien matalan kynnyksen kohtaamispaikka", C.COMMUNITY_CENTRE, _SKIP),
    ("Nuorten ja nuorten aikuisten kohtaamispaikka JOJO", C.COMMUNITY_CENTRE, _SKIP),
    ("Koloveden luontotupa ja matkailuneuvonta", C.COMMUNITY_CENTRE, _SKIP),
    ("ViaDian Kohtaamisasema", C.COMMUNITY_CENTRE, _SKIP),
    ("Miesten asema", C.COMMUNITY_CENTRE, _SKIP),
    ("Keiteleen seurakuntatalo", C.COMMUNITY_CENTRE, _SKIP),
    ("Karhuvuoren seurakuntakoti", C.COMMUNITY_CENTRE, _SKIP),
    ("Lahjanpuiston kerhohuone", C.COMMUNITY_CENTRE, _SKIP),
    ("Linnainmaan seurakuntakeskus", C.COMMUNITY_CENTRE, _SKIP),
    ("Seurakuntatila Kauksun Kulma", C.COMMUNITY_CENTRE, _SKIP),
    ("Kulttuuritalo Kimara", C.COMMUNITY_CENTRE, _SKIP),
    ("Itätuulen 4H-kerho", C.COMMUNITY_CENTRE, _SKIP),
    ("4H-kerho", C.COMMUNITY_CENTRE, _SKIP),
    ("Harrastetilat", C.COMMUNITY_CENTRE, _SKIP),
]


@pytest.mark.parametrize("fi,want_cat,want_extra", _COMMUNITY_CASES)
def test_category_community(fi, want_cat, want_extra):
    check_cat(fi, want_cat, want_extra)


# ---- Categories: leisure and sport ----------------------------------------------------
C = Categories

_LEISURE_CASES = [
    # School-hosted sports file as sports.
    ("Saunalahden koulun hiekkakenttä", C.LEISURE_PITCH, _SKIP),
    ("Kaasmarkun koulun kaukalo", C.LEISURE_ICE_RINK, _SKIP),
    ("Kuusikon koulun luistelukenttä", C.LEISURE_ICE_RINK, _SKIP),
    ("Lietsalan koulun liikuntasali", C.LEISURE_SPORTS_HALL, _SKIP),
    ("Tiedonpuiston koulun liikuntatilat", C.LEISURE_SPORTS_HALL, _SKIP),
    ("Opinmäen koulun liikuntahalli", C.LEISURE_SPORTS_CENTRE, _SKIP),
    ("Uittamon koulun sali", C.LEISURE_SPORTS_HALL, _SKIP),
    ("Hirvaskosken koulun frisbeegolfrata", C.LEISURE_DISC_GOLF_COURSE, _SKIP),
    ("Nurmikenttä 1", C.LEISURE_PITCH, _SKIP),
    (
        "Leppävaaran urheilupuiston tekonurmikenttä 2",
        C.LEISURE_PITCH,
        {"sport": "soccer", "surface": "artificial_turf"},
    ),
    ("Lounatuulenpuiston koripallokenttä", C.LEISURE_PITCH, _SKIP),  # sport=basketball pinned below
    ("Haminamäen Valio Areenan nurmikenttä", C.LEISURE_PITCH, _SKIP),
    ("Tenniskentät", C.LEISURE_PITCH, {"sport": "tennis"}),
    ("Kangaslammin nurmikentät", C.LEISURE_PITCH, _SKIP),
    ("Vasaramäen koulu, Tenniskentän yksikkö", C.LEISURE_PITCH, _SKIP),
    ("Kulomäen lähiliikuntapaikan miniareena", C.LEISURE_PITCH, _SKIP),
    ("Pallopuiston lähiliikuntapaikan tenniskenttä", C.LEISURE_PITCH, {"sport": "tennis"}),
    (
        "Jokivarren koulun lähiliikuntapaikan tekonurmi",
        C.LEISURE_PITCH,
        {"sport": "soccer", "surface": "artificial_turf"},
    ),
    ("Tikkakosken liikuntapuiston beach volley -kenttä", C.LEISURE_PITCH, _SKIP),
    ("Velaatan uimarannan beach volley -kenttä", C.LEISURE_PITCH, _SKIP),
    ("Säkyläpadel", C.LEISURE_PITCH, {"sport": "padel"}),
    ("Padel-kentät", C.LEISURE_PITCH, {"sport": "padel"}),
    ("Ukonniemen ulkopadelkenttä", C.LEISURE_PITCH, {"sport": "padel"}),
    ("Seikkailutalon piha-alueen kiipeilypisteet", C.LEISURE_PITCH, {"sport": "climbing"}),
    ("Shakkilauta, Hesperianpuisto", C.LEISURE_PITCH, {"sport": "chess"}),
    ("Shakkilaudat, Hakasalmenpuisto", C.LEISURE_PITCH, {"sport": "chess"}),
    ("Katajanokan liikuntahalli / Yhden korin koripallokenttä", C.LEISURE_PITCH, _SKIP),
    ("Hietarannan uimaranta / Koripallokenttä", C.LEISURE_PITCH, _SKIP),
    ("Väinämöisenkenttä / Huoltorakennus", C.LEISURE_PITCH, _SKIP),
    ("Landbonkenttä / Lähiliikuntapaikka (Miniareena)", C.LEISURE_PITCH, _SKIP),
    ("Saarikenttä- pesäpallostadion", _SKIP, {"sport": "pesapallo"}),
    ("Pisanpuiston petanque-kenttä", _SKIP, {"sport": "petanque"}),
    ("Kurkvuoren moottoriurheilualue", C.LEISURE_PITCH, {"sport": "motor"}),
    ("Yleisurheilukenttä", C.LEISURE_TRACK, _SKIP),
    ("Pump track-rata", C.LEISURE_TRACK, _SKIP),
    # Halls, pools, ice, gyms.
    ("Uintikeskus", C.LEISURE_SPORTS_CENTRE, _SKIP),
    ("Uimahalli", C.LEISURE_SPORTS_CENTRE, {"sport": "swimming"}),
    ("Keravan maauimala", C.LEISURE_SPORTS_CENTRE, {"sport": "swimming"}),
    ("Savitaipaleen liikuntatalo", C.LEISURE_SPORTS_CENTRE, _SKIP),
    ("Kämärin jääurheilukeskus", C.LEISURE_SPORTS_CENTRE, _SKIP),
    # Ski centres read as sports centres, not generic.
    ("Kusiaismäen hiihtokeskus", C.LEISURE_SPORTS_CENTRE, _SKIP),
    ("Keimolan kilpahiihtokeskus", C.LEISURE_SPORTS_CENTRE, _SKIP),
    ("Honkalan hiihtokeskus", C.LEISURE_SPORTS_CENTRE, _SKIP),
    ("Melonta Kaartjärvellä", C.LEISURE_SPORTS_CENTRE, _SKIP),
    ("Kaukajärven soutu- ja melontastadion", C.LEISURE_SPORTS_CENTRE, _SKIP),
    ("Yli-Iin yleisurheilukeskus", C.LEISURE_SPORTS_CENTRE, {"sport": "athletics"}),
    ("Maunulan liikuntahalli / Sisäampumarata", C.LEISURE_SPORTS_CENTRE, _SKIP),
    ("Säkylähalli", C.LEISURE_SPORTS_HALL, _SKIP),
    ("Talviharjoitteluhalli", C.LEISURE_SPORTS_HALL, _SKIP),
    ("Hämeenkylän päiväkodin liikuntasali", C.LEISURE_SPORTS_HALL, _SKIP),
    ("Sangin vanhan koulun liikuntasali", C.LEISURE_SPORTS_HALL, _SKIP),
    ("Kampuksen kamppailutila", C.LEISURE_SPORTS_HALL, _SKIP),
    ("Mikkelin jäähalli", C.LEISURE_ICE_RINK, _SKIP),
    ("Keilahalli", C.LEISURE_BOWLING_ALLEY, _SKIP),
    ("Itäkeskuksen uimahalli / Liikuntasali", C.GYM, _SKIP),
    ("Sportis gym", C.GYM, _SKIP),
    ("Fitness Center", C.GYM, _SKIP),
    ("Ahtialan työväentalon kuntosali", C.GYM, _SKIP),
    ("Kuntosali yhdistyksen jäsenille", C.GYM, _SKIP),
    ("Kuntosali, ryhmä 1", C.GYM, _SKIP),
    ("Hietarannan uimaranta / Ulkokuntoilupaikka (Keski)", C.LEISURE_FITNESS_STATION, _SKIP),
    ("Kirkkokallion kuntoportaat", C.LEISURE_FITNESS_STATION, _SKIP),
    ("Jokiuomanpuiston kuntoilupaikka", C.LEISURE_FITNESS_STATION, _SKIP),
    ("Vanhan-Mankkaan puiston kuntoilupiste 1", C.LEISURE_FITNESS_STATION, _SKIP),
    ("Lähiliikuntapaikka", C.LEISURE_FITNESS_STATION, _SKIP),
    ("Espoon Kirkkojärven skeittipaikka", C.LEISURE_PITCH, _SKIP),
    ("Rauma DiscGolfPark", C.LEISURE_DISC_GOLF_COURSE, _SKIP),
    ("Golfkenttä", C.LEISURE_GOLF_COURSE, _SKIP),
    # Playgrounds and schoolyards read as playgrounds.
    ("Varikkotien leikkikenttä", C.LEISURE_PLAYGROUND, _SKIP),
    ("Leikkipaikka Tokoinranta", C.LEISURE_PLAYGROUND, _SKIP),
    ("Hovirinnan Rantaleikkipuisto", C.LEISURE_PLAYGROUND, _SKIP),
    ("Rantapuiston Leikkikenttä", C.LEISURE_PLAYGROUND, _SKIP),
    ("Åshöjdens grundskola / Lähiliikuntapaikka", C.LEISURE_PLAYGROUND, _SKIP),
    ("Porolahden peruskoulu / Lähiliikuntapaikka", C.LEISURE_PLAYGROUND, _SKIP),
    ("Lapijoen päiväkodin lähiliikuntapaikka", C.LEISURE_PLAYGROUND, _SKIP),
    ("Ilolan koulun lähiliikuntapaikka", C.LEISURE_PLAYGROUND, _SKIP),
    # Beaches, swim holes, dog beaches.
    ("Jänissaaren uimapaikka", C.NATURAL_BEACH, None),
    ("Uimarannat", C.NATURAL_BEACH, _SKIP),
    ("Pakilan uimaranta", C.NATURAL_BEACH, _SKIP),
    ("Munkkiniemen uimaranta", C.NATURAL_BEACH, _SKIP),
    ("Munkkiniemen uimaranta / Huoltorakennus", C.NATURAL_BEACH, _SKIP),
    ("Lauttasaaren uimaranta / Beachvolleykenttä", _SKIP, {"sport": "beachvolleyball"}),
    ("Ourit (Talviuimarit)", C.LEISURE_SWIMMING_AREA, _SKIP),
    ("Talviuimaranta", C.LEISURE_SWIMMING_AREA, _SKIP),
    ("Haaruksen Jämä-majan avanto", C.LEISURE_SWIMMING_AREA, _SKIP),
    ("Toppelundinrannan koirauimaranta", C.LEISURE_DOG_PARK, _SKIP),
    ("Koiratarha", C.LEISURE_DOG_PARK, _SKIP),
    ("Hundparken", C.LEISURE_DOG_PARK, _SKIP),
    # Boats, marinas, slipways, fishing.
    ("Saunalahden venesatama", C.MARINA, _SKIP),
    ("Venesatamat", C.MARINA, _SKIP),
    ("Sirkkakosken vene- ja kalasatama", C.MARINA, _SKIP),
    ("Loppijärvi, Kuljun veneranta", C.MARINA, _SKIP),
    ("Halsuan keskustan uimaranta ja veneranta", C.MARINA, _SKIP),
    ("Veneranta, Leppävesi", C.MARINA, _SKIP),
    ("Tuomalan rannan venepaikat", C.MARINA, _SKIP),
    ("Kaupunkisoutuveneet", C.AMENITY_BOAT_RENTAL, _SKIP),
    ("Ipo-Kiusalan veneenlaskupaikka", C.LEISURE_SLIPWAY, _SKIP),
    ("Salmen ulkoilualue / Kalastuspaikka", _SKIP, {"leisure": "fishing"}),
    ("Arabianranta / Kalastuspaikka", _SKIP, {"leisure": "fishing"}),
    ("Eläintarhanlahti ja Tokoinranta / Kalastuspaikka", _SKIP, {"leisure": "fishing"}),
    ("Tikkurilankosken kalastuslupa-alue", _SKIP, {"leisure": "fishing"}),
    ("Mykänlammen virkistys ja kalastusalue", _SKIP, {"leisure": "fishing"}),
    ("Kalastuspaikan vuokraus", None, {"leisure": "fishing"}),
    # Shooting grounds (never fixed orienteering controls).
    ("Ampumarata", _SKIP, {"leisure": "shooting_ground", "sport": "shooting"}),
    ("Ampumaradat", _SKIP, {"leisure": "shooting_ground", "sport": "shooting"}),
]


@pytest.mark.parametrize("fi,want_cat,want_extra", _LEISURE_CASES)
def test_category_leisure(fi, want_cat, want_extra):
    check_cat(fi, want_cat, want_extra)


def test_court_keeps_sport():
    # Pallokenttä shadowed koripallo until the reorder; spaced beach-volley
    # compounds carry beachvolleyball.
    category, extra = cat(make_spider(), "Lounatuulenpuiston koripallokenttä")
    assert category == C.LEISURE_PITCH
    assert extra["sport"] == "basketball"
    category, extra = cat(make_spider(), "Koripallohalli")
    assert extra["sport"] == "basketball"
    for fi in (
        "Tikkakosken liikuntapuiston beach volley -kenttä",
        "Velaatan uimarannan beach volley -kenttä",
    ):
        category, extra = cat(make_spider(), fi)
        assert category == C.LEISURE_PITCH, fi
        assert extra["sport"] == "beachvolleyball", fi


# ---- Categories: outdoors, tourism, culture, infra ----------------------------------

_PLACE_CASES = [
    # Camp stays camp.
    ("Vuolahden leirialue", C.TOURISM_CAMP_SITE, _SKIP),
    ("Rastilan leirintäalue", C.TOURISM_CAMP_SITE, _SKIP),
    ("Gåsgrund / Telttailupaikka", C.TOURISM_CAMP_SITE, _SKIP),
    ("Telttailu- ja leiriytymispaikka 1", C.TOURISM_CAMP_SITE, _SKIP),
    ("Näätähiekan leirikeskus", C.TOURISM_CAMP_SITE, _SKIP),
    # Parks, picnic, shelters, wilderness.
    ("Salmen ulkoilualue / Taukotupa", C.LEISURE_PARK, _SKIP),
    ("Kauko Kortelaisen veistospuisto", C.LEISURE_PARK, _SKIP),
    # The puistikko diminutive reads as a park; park-road addresses don't.
    ("Lentäjänpuistikko", C.LEISURE_PARK, _SKIP),
    ("Seurasaari / Grillipaikka", C.TOURISM_PICNIC_SITE, _SKIP),
    ("Meri-Rastila / Grillipaikka", C.TOURISM_PICNIC_SITE, _SKIP),
    ("Malmin kenttä / Väliaikainen grillipaikka", C.TOURISM_PICNIC_SITE, _SKIP),
    ("Vareskota", C.SHELTER, _SKIP),
    ("Grillikatokset- ja kodat", C.SHELTER, _SKIP),
    ("Niemisjärven kalastusalueen laavu (Evo)", C.SHELTER, _SKIP),
    ("Tervanapsu autiotupa", C.TOURISM_WILDERNESS_HUT, _SKIP),
    ("Marjapensaspaikka", C.ALLOTMENTS, _SKIP),
    ("Käräjätuvan- ja Näsinojankuja, viljelypalstat", C.ALLOTMENTS, _SKIP),
    # Art and memorials.
    ("Juhannussalko", C.TOURISM_ARTWORK, _SKIP),
    ('Taideteos "Turvapaikka" osa 1', C.TOURISM_ARTWORK, _SKIP),
    ("Lausteen taidekontti", C.TOURISM_ARTWORK, _SKIP),
    ("Taidekontit ja graffitiseinä", _SKIP, {"artwork_type": "graffiti"}),
    ("Musta graniittiveistos", None, {"tourism": "artwork", "artwork_type": "sculpture"}),
    ("Lastenkulttuurikeskus", C.ARTS_CENTRE, _SKIP),
    ("Taiteen perusopetus", C.ARTS_CENTRE, _SKIP),
    ("Lastenkulttuurikeskus Pyykkitupa", C.ARTS_CENTRE, _SKIP),
    ("Raatihuone, raatihuonegalleria", C.ARTS_CENTRE, _SKIP),
    # Stages and screens.
    ("Lilla Teatern", C.THEATRE, _SKIP),
    ("Teaterstudio Pasila", C.THEATRE, _SKIP),
    ("Stoa / Teatterisali", C.THEATRE, _SKIP),
    ("Konserttitalo", C.EVENTS_VENUE, _SKIP),
    ("Konsertti- ja kongressitalo Mikaeli", C.EVENTS_VENUE, _SKIP),
    ("Tapahtumatalo", C.EVENTS_VENUE, _SKIP),
    ("Tapahtuma-alue", C.EVENTS_VENUE, _SKIP),
    ("Tapahtumalava", C.EVENTS_VENUE, _SKIP),
    ("Auditorio", C.EVENTS_VENUE, _SKIP),
    ("Aleksis Kiven peruskoulu / Juhlasali", C.EVENTS_VENUE, _SKIP),
    ("Stoa / Musiikkisali", C.EVENTS_VENUE, _SKIP),
    ("Valtuustosali", C.EVENTS_VENUE, _SKIP),
    ("Pengerpuisto, tapahtuma-alue", C.EVENTS_VENUE, _SKIP),
    # Faith, cemeteries, attractions, viewpoints.
    ("Aurejärven kirkko", C.PLACE_OF_WORSHIP, _SKIP),
    ("Pielaveden kirkko", C.PLACE_OF_WORSHIP, {"religion": "christian", "denomination": "lutheran"}),
    ("Lepolan hautausmaan kappeli", C.PLACE_OF_WORSHIP, _SKIP),
    ("Riihimäen hautausmaan toimisto", C.OFFICE_GOVERNMENT, _SKIP),
    ("Pieneläinten hautausmaa", _SKIP, {"landuse": "cemetery"}),
    ("Pieneläinhautausmaa", _SKIP, {"landuse": "cemetery"}),
    ("Korkeasaaren eläintarha", _SKIP, {"tourism": "zoo"}),
    ("Koivuhaan lammasaitaus", C.TOURISM_ATTRACTION, _SKIP),
    ("Purasjoen puolustusasema 1939", C.TOURISM_ATTRACTION, _SKIP),
    ("Vaarniemen näköalatorni", C.TOURISM_VIEWPOINT, {"man_made": "tower", "tower:type": "observation"}),
    ("Viikki-Vanhankaupunginlahti, Lammassaaren esteetön lintulava", C.TOURISM_VIEWPOINT, _SKIP),
    ("Ison Vasikkasaaren luontotorni", C.TOURISM_VIEWPOINT, _SKIP),
    ("Sörnäisten metroaseman yleinen väestönsuoja", C.MILITARY_BUNKER, {"bunker_type": "bomb_shelter"}),
    ("Kampin metroaseman yleinen väestönsuoja", C.MILITARY_BUNKER, _SKIP),
    ("Salpalinjan teräsbetoninen korsu", C.MILITARY_BUNKER, None),
    ("Lehtisaaren yhteiskalliosuoja", C.MILITARY_BUNKER, _SKIP),
    ("Villaluodot Läntinen saari", _SKIP, {"place": "island"}),
    ("Malkasaari (saari)", _SKIP, {"place": "island"}),
    ("Kotiluoto (saari)", _SKIP, {"place": "island"}),
    ("Tiirakari (saari)", _SKIP, {"place": "island"}),
    ("Talvipuutarha", None, {"leisure": "botanical_garden"}),
    ("Kasvitieteellinen puutarha", None, {"leisure": "botanical_garden"}),
    ("Koivuhaan arboretum", None, {"leisure": "botanical_garden"}),
    ("Lapinlahden Erikoismetsä", _SKIP, {"natural": "wood"}),
    ("Lumenkaatopaikka", _SKIP, {"landuse": "landfill"}),
    ("Pielaveden maankaatopaikka", _SKIP, {"landuse": "landfill"}),
    # Tourist info desks (never generic offices).
    ("Infopiste", C.TOURISM_INFORMATION, _SKIP),
    ("Pääinfo", C.TOURISM_INFORMATION, _SKIP),
    ("Talin liikuntapuisto / Opastuspiste", C.TOURISM_INFORMATION, _SKIP),
    ("Matkailuneuvontapiste Sulkavalla", C.TOURISM_INFORMATION, _SKIP),
    ("Laitilan matkailuinfopiste", C.TOURISM_INFORMATION, _SKIP),
    ("Visit Pori Matkailuneuvonta", C.TOURISM_INFORMATION, _SKIP),
    ("Matkailuinfon toimipiste", C.TOURISM_INFORMATION, _SKIP),
    ("Matkailuneuvonnan palvelupiste", C.TOURISM_INFORMATION, _SKIP),
    ("Saimaa Geopark visitor center", C.TOURISM_INFORMATION, {"information": "visitor_centre"}),
    ("Saimaa Geopark visitor centre", C.TOURISM_INFORMATION, {"information": "visitor_centre"}),
    ("Korkeasaaren eläintarhan lipunmyynti", _SKIP, {"shop": "tickets"}),
    ("Lahden kaupunginteatterin lippumyymälä", _SKIP, {"shop": "tickets"}),
    ("Roihupellon myymälä, Stadin ammattiopisto", _SKIP, {"shop": "yes"}),
    # Food, drink, everyday infra.
    ("Ravintola Dakota", C.RESTAURANT, _SKIP),
    ("Jorvin Terassikahvio", C.CAFE, _SKIP),
    ("Topeliuksen puiston yleisövessa", C.TOILETS, _SKIP),
    ("Kuusijärven saunat", C.SAUNA, _SKIP),
    ("Vesipiste veneilijöille", C.DRINKING_WATER, _SKIP),
    ("Pielaveden kunnan yleinen vedenjakelupiste", C.DRINKING_WATER, _SKIP),
    ("Virolahden kunnan vesiposti Virojoella", C.DRINKING_WATER, _SKIP),
    ("Kokkomäen puutarhajätealue", C.RECYCLING, _SKIP),
    ("Korvenmäen jätekeskus", C.RECYCLING, _SKIP),
    ("Kempeleen vaarallisen jätteen vastaanotto", C.RECYCLING, _SKIP),
    ("Perniön lajitteluasema", C.RECYCLING, _SKIP),
    ("Tervolan Ekoasema", C.RECYCLING, _SKIP),
    ("Vaarallisten jätteiden autokeräys", C.RECYCLING, _SKIP),
    ("Kiertopisteen materiaali- ja tekstiilipankki", C.RECYCLING, _SKIP),
    ("Taavetin Hyödyksi-asema", C.RECYCLING, _SKIP),
    ("Sähköauton latauspiste", C.CHARGING_STATION, _SKIP),
    ("Sähköauton latauspiste, Nuottaniemen venesatama", C.CHARGING_STATION, _SKIP),
    ("Esteetön pysäköintialue Kivenlahdentori", C.PARKING, _SKIP),
    ("Kauppatori", C.MARKETPLACE, _SKIP),
    ("Töölöntori", _SKIP, {"place": "square"}),
    ("Senaatintori", _SKIP, {"place": "square"}),
    ("Kiuruveden tori", None, _SKIP),
    ("Hansaterminaali", C.FERRY_TERMINAL, _SKIP),
    ("Länsiterminaali 1", C.FERRY_TERMINAL, _SKIP),
    ("Kaupunginpuutarhan talkoolaituri", C.TOOL_LIBRARY, _SKIP),
    ("Keski-Espoon urheilupuisto 2.", C.LEISURE_SPORTS_CENTRE, _SKIP),
    # Stations and civic guards.
    ("Vehkalan asema", _SKIP, {"railway": "station", "public_transport": "station"}),
    ("Kampin metroasema", _SKIP, {"railway": "station", "public_transport": "station"}),
    ("Leinelän asema", _SKIP, {"railway": "station", "public_transport": "station"}),
    ("Lentoaseman rautatieasema", _SKIP, {"railway": "station", "public_transport": "station"}),
    ("Linja-autoasema", C.BUS_STATION, _SKIP),
    ("Paloasema", C.FIRE_STATION, _SKIP),
    ("Mellunkylän pelastusasema", C.FIRE_STATION, _SKIP),
    ("Kiviniemen VPK", C.FIRE_STATION, _SKIP),
    ("Kakskerran Sopimuspalokunta", C.FIRE_STATION, _SKIP),
    ("Krossin pelastus- ja ensihoitoasema", C.FIRE_STATION, _SKIP),
    ("Joensuun krematorio", _SKIP, {"amenity": "crematorium"}),
    ("Krematorio", _SKIP, {"amenity": "crematorium"}),
    ("Kunnanvarikko", _SKIP, {"amenity": "depot"}),
    ("Vantaan kaupungin varikko", _SKIP, {"amenity": "depot"}),
    ("Nuorisotila Varikko", _SKIP, {"amenity": "youth_centre"}),
    ("Punkalaitumen Nuorisotila", None, {"amenity": "youth_centre"}),
    ("Puokkarin nuokkari", _SKIP, {"amenity": "youth_centre"}),
    ("Sökö ungdomslokal", _SKIP, {"amenity": "youth_centre"}),
    ("Nuorisotilat ja -toimisto", None, {"amenity": "youth_centre"}),
    ("Pudasjärven Ilmailukeskus", _SKIP, {"aeroway": "aerodrome"}),
    ("Porvoon kissatalo", _SKIP, {"amenity": "animal_shelter"}),
    ("Löytöeläimet Eura", _SKIP, {"amenity": "animal_shelter"}),
    ("Porin löytökissat", _SKIP, {"amenity": "animal_shelter"}),
    ("Agricolanpuistikon koirakäymälä", _SKIP, {"amenity": "dog_toilet"}),
]


@pytest.mark.parametrize("fi,want_cat,want_extra", _PLACE_CASES)
def test_category_places(fi, want_cat, want_extra):
    check_cat(fi, want_cat, want_extra)


# ---- Categories: untyped stays untyped -------------------------------------------------

_GENERIC_CASES = [
    ("Leikkivät karhut", None, None),
    ("Pelataan yhdessä shakkia", None, None),
    ("Uimakoulut", None, _SKIP),
    ("Ikäihmisten liikunta", None, None),
    ("Keskuspuiston kiintorastit", None, None),
    ("Viherkallion asukaspuiston kerho", None, None),
    ("Melontareitti", None, None),
    ("Väriaattori", None, None),
    ("Sastamala omatoiminen kuntosaliryhmä omaishoitajille", None, None),
    ("Laiturin Iloa ikäihmisille-ryhmä, Utra", None, None),
    ("Jyränkölön Setlementti Sireniussalin ystäväryhmä", None, None),
    ("Anniksen enkelit -teatteriryhmä", None, _SKIP),
    ("Miesten kirjastoparlamentti", None, _SKIP),
    ("Tapahtumayksikkö", None, _SKIP),
    ("Jäsentapahtumat ja luennot", None, _SKIP),
    ("Joen Severin digiopastus", None, _SKIP),
    ("Joen Severin digiopastus Karsikon kirjastolla", None, _SKIP),
    ("Testausasema", None, None),
    ("Kalasatama", None, _SKIP),
    ("Huoltoasema", None, _SKIP),
    ("Hallitus", None, _SKIP),
    ("Tullinkulma", None, _SKIP),
    ("Tullikamari", None, _SKIP),
    ("Tullinaukio", None, _SKIP),
    ("Asematien Pysäkki", None, None),
    ("Eläintarhan huvila", None, _SKIP),
    ("Martat neuvoo Kuusankosken kirjastossa", None, _SKIP),
    ("Sinfonia", None, _SKIP),
    ("Rulla", None, _SKIP),
    ("Saarentie 5", None, _SKIP),
]


@pytest.mark.parametrize("fi,want_cat,want_extra", _GENERIC_CASES)
def test_category_generic(fi, want_cat, want_extra):
    check_cat(fi, want_cat, want_extra)


def test_camp_track_gate_pin():
    # Table-level only: the exact pururata name never emits, the track gate
    # drops fitness trails before categorising.
    spider = make_spider()
    assert cat(spider, "Lankarin leirikeskuksen pururata")[0] == C.TOURISM_CAMP_SITE
    assert spider._is_dropped_name(spider._clean_name("Lankarin leirikeskuksen pururata")) == "non_place/track"


def test_parking_machine_with_payment():
    category, extra = cat(make_spider(), "Pysäköintilippuautomaatti 322, Töölöntori, korttimaksu")
    assert category == C.VENDING_MACHINE
    assert extra["vending"] == "parking_tickets"
    assert extra["payment:credit_cards"] == "yes"
    assert cat(make_spider(), "Pysäköintilippuautomaatti 630, Krematoriontie, korttimaksu")[0] == C.VENDING_MACHINE


def test_church_denomination_scoped():
    category, extra = cat(make_spider(), "Pielaveden kirkko")
    assert category == C.PLACE_OF_WORSHIP
    assert extra == {"religion": "christian", "denomination": "lutheran"}


def test_kirkko_compound_end_only():
    check_cat("Aurejärven kirkko", C.PLACE_OF_WORSHIP)
    check_cat("Espoon Kirkkojärven skeittipaikka", C.LEISURE_PITCH)
    check_cat("Kirkkokallion kuntoportaat", C.LEISURE_FITNESS_STATION)


# ---- Rescue and fallback ------------------------------------------------------------
# Opaque proper names type via linked services, ontology terms and
# descriptions. Name tier always wins; generic admin labels never shadow
# specific services; placement-only extras never rescue a venue filing.


def test_rescue_from_descriptions():
    spider = make_spider()
    housing = {
        "serviceChannelDescriptions": [
            {"language": "fi", "value": "Naskali tarjoaa asumista ja siihen liittyviä palveluita kehitysvammaisille."}
        ]
    }
    assert spider._rescue_category(housing) == Categories.ASSISTED_LIVING
    social = {"serviceChannelDescriptions": [{"language": "fi", "value": "Päivätoimintaa kehitysvammaisille."}]}
    assert spider._rescue_category(social) == Categories.SOCIAL_FACILITY
    art = {"serviceChannelDescriptions": [{"language": "fi", "value": "Essi Renvallin Kala ja poika -veistos."}]}
    assert spider._rescue_category(art) == Categories.TOURISM_ARTWORK
    assert (
        spider._rescue_category({"serviceChannelDescriptions": [{"language": "fi", "value": "Avoinna arkisin."}]})
        is None
    )
    assert spider._rescue_category({}) is None
    # Needs assessments never house; tuettu-proximity still houses.
    ch = channel("Palveluneuvonta")
    ch["serviceChannelDescriptions"] = [
        {"language": "fi", "value": "mielenterveys- ja asumispalvelujen tarpeen arviointi"}
    ]
    assert spider._rescue_category(ch) == Categories.SOCIAL_FACILITY
    ch2 = channel("Palveluneuvonta")
    ch2["serviceChannelDescriptions"] = [{"language": "fi", "value": "mielenterveyskuntoutujien tuettu asuminen"}]
    assert spider._rescue_category(ch2) == Categories.ASSISTED_LIVING


def test_rescue_from_services_and_ontology():
    spider = make_spider()
    # Opaque name via its linked service name.
    ch = channel("Maya")
    ch["services"] = [{"service": {"name": "Maya tukiasunto Pietarsaaressa"}}]
    assert parsed(spider, ch)["extras"]["social_facility"] == "assisted_living"
    # Admin-shaped services fall through to YSO ontology terms.
    ch = channel("Maya")
    ch["services"] = [{"service": {"name": "Liikunnan ja urheilun tulosyksikkö"}}]
    ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": "päiväkotihoito"}]}]
    assert parsed(spider, ch).get_tag("amenity") == "kindergarten"
    # Placement-only rescue carries tags without a POI category.
    ch = channel("Maya")
    ch["services"] = [{"service": {"name": "Eläintarhan myymälä"}}]
    assert parsed(spider, ch)["extras"]["shop"] == "yes"
    # Supported housing beats diagnosis at the POI.
    ch = channel("Etu-Töölön asuintalo")
    ch["services"] = [{"service": {"name": "Mielenterveyskuntoutujien tuettu asuminen"}}]
    item = parsed(spider, ch)
    assert item.get_tag("amenity") == "social_facility"
    assert item["extras"].get("social_facility") == "assisted_living"
    # Desk-shaped opaque names rescue, care homes keep theirs.
    ch = channel("Pirtin Kohtaamo")
    ch["services"] = [
        {"service": {"name": "Kunnan viralliset ilmoitukset"}},
        {"service": {"name": "Asiakaspalvelu"}},
        {"service": {"name": "Kelan asiointipiste Pudasjärvellä"}},
    ]
    assert parsed(spider, ch).get_tag("office") == "government"
    ch = channel("Kolpeneen tuki- ja osaamiskeskus")
    ch["services"] = [{"service": {"name": "Kuntoutusohjaus- ja asiantuntijapalvelut"}}]
    assert parsed(spider, ch).get_tag("amenity") == "social_facility"
    ch = channel("OYS Konsti")
    ch["services"] = [{"service": {"name": "Vaativat kehitysvammapalvelut"}}]
    assert parsed(spider, ch).get_tag("amenity") == "social_facility"


def test_rescue_skips_generic_labels_and_activities():
    spider = make_spider()
    # "Varhaiskasvatus" files as an office, so it must not shadow the
    # specific ontology behind it. Activity groups never rescue either.
    for name in ("Lastentalo Kuusipiha", "Satukontti"):
        ch = channel(name)
        ch["services"] = [{"service": {"name": "Varhaiskasvatus"}}]
        ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": "päiväkotihoito"}]}]
        assert parsed(spider, ch).get_tag("amenity") == "kindergarten", name
    for name in ("Laiturin Iloa ikäihmisille-ryhmä, Utra", "Sastamala omatoiminen kuntosaliryhmä omaishoitajille"):
        ch = channel(name)
        ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": "mielenterveys"}]}]
        assert spider._rescue_service(ch) is None, name
    # Peer-delivered support never rescues to clinic.
    ch = channel("Suvanto-vertaistiimi")
    ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": "mielenterveys"}]}]
    assert spider._rescue_service(ch) is None
    # Care-named activities stay generic; mental-health purpose doesn't clinic them.
    ch = channel("Nakkifiesta")
    ch["services"] = [{"service": {"name": "Nakkifiesta"}}]
    ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": "mielenterveys"}]}]
    assert parsed(spider, ch).get_tag("amenity") == "yes"


def test_rescue_placement_extras_never_type():
    # Catalogue placement tags cannot type opaque channels; real venue
    # services still rescue.
    spider = make_spider()
    ch = channel("Oittaan pulkkamäki")
    ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": "ampumaradat"}]}]
    assert spider._rescue_service(ch) is None
    ch = channel("Finlandia-talo")
    ch["services"] = [{"service": {"name": "Lipunmyynti kulttuuri- ja taidetapahtumiin"}}]
    assert spider._rescue_service(ch) is None
    ch = channel("Raatihuone")
    ch["services"] = [{"service": {"name": "Tori- ja katumyyntipaikkojen vuokraus"}}]
    assert spider._rescue_service(ch) is None
    ch = channel("Motocross- ja enduroradat")
    ch["services"] = [{"service": {"name": "Muukon moottori- ja ampumaurheilukeskus"}}]
    assert spider._rescue_service(ch)[0] == Categories.LEISURE_SPORTS_CENTRE
    ch = channel("Espoon Rantaraitti")
    assert spider._rescue_blocked(ch)
    ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": "pallokentät"}]}]
    assert parsed(spider, ch).get_tag("leisure") is None
    ch = channel("Espoon Rantaraitti")
    ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": v}]} for v in ("ampumaradat", "kavelyreitit")]
    assert spider._rescue_service(ch) is None


def test_rescue_routes_trails_and_islands():
    spider = make_spider()
    ch = channel("Otaniemen kiintorastit")
    ch["services"] = [{"service": {"name": "Liikunnan ja urheilun tulosyksikkö"}}]
    ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": "ampumaradat"}]}]
    item = parsed(spider, ch)
    assert item.get_tag("amenity") == "yes"
    assert item.get_tag("leisure") is None
    ch = channel("Porsas")
    ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": "ulkoilusaaret"}]}]
    assert spider._rescue_service(ch) is None
    ch = channel("Porsas")
    ch["services"] = [{"service": {"name": "Ulkoilusaaret"}}]
    assert spider._rescue_service(ch) == (None, {"place": "island"})
    ch = channel("Porsas")
    ch["services"] = [{"service": {"name": "Haltialan kotieläintila"}}, {"service": {"name": "Ulkoilusaaret"}}]
    assert parsed(spider, ch)["extras"].get("place") == "island"
    # Supported housing next to a diagnosis rescues assisted living.
    ch = channel("Tervahovin asunnot")
    ch["services"] = [{"service": {"name": "Tuettu asuminen, vammaispalvelut"}}]
    ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": "palveluasuminen"}]}]
    assert spider._resolve_fallback_category(Feature(), ch) == Categories.ASSISTED_LIVING


def test_rescue_multilingual_and_special_hosts():
    spider = make_spider()
    # Public art documented outside Finnish still rescues.
    ch = channel("Eino Leino")
    ch["serviceChannelDescriptions"] = [
        {"language": "fi", "value": "Eino Leino julkista taidetta."},
        {"language": "en", "value": "Eino Leino is a work of public art."},
    ]
    assert parsed(spider, ch).get_tag("tourism") == "artwork"
    # Memorial sv/en names type the opaque fi one.
    ch = channel("Mortuis")
    ch["serviceChannelNames"] = [
        {"language": "fi", "value": "Mortuis", "type": "Name"},
        {"language": "sv", "value": "Mortius, minnesmärke över explosionen", "type": "Name"},
        {"language": "en", "value": "Mortuis memorial", "type": "Name"},
    ]
    item = parsed(spider, ch)
    assert item.get_tag("tourism") == "artwork"
    assert "place" not in item["extras"]
    # Disability-ontology competence centres rescue social, never islands.
    ch = channel("Osaamiskeskus, Pietarsaari")
    ch["services"] = [{"service": {"name": "Osaamiskeskus"}}]
    ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": "kehitysvammaiset"}]}]
    item = parsed(spider, ch)
    assert item.get_tag("amenity") == "social_facility"
    assert "place" not in item["extras"]
    # Island-titled public art files as art.
    ch = channel("Saari")
    ch["services"] = [{"service": {"name": "Julkinen taide"}}]
    ch["ontologyTerms"] = [
        {"name": [{"language": "fi", "value": "julkinen taide"}]},
        {"name": [{"language": "fi", "value": "veistokset"}]},
    ]
    assert parsed(spider, ch)["extras"].get("tourism") == "artwork"
    # Swedish daycare names type opaque fi ones.
    ch = channel("Karitsa")
    ch["serviceChannelNames"] = [
        {"language": "fi", "value": "Karitsa", "type": "Name"},
        {"language": "sv", "value": "Daghemmet Karitsa", "type": "Name"},
    ]
    assert parsed(spider, ch).get_tag("amenity") == "kindergarten"
    # Wellbeing-area school words are the student-health unit.
    assert parsed(spider, channel("Joutsan lukio"), "Keski-Suomen hyvinvointialue").get_tag("amenity") == "clinic"
    assert parsed(spider, channel("Lukio"), "Keski-Suomen hyvinvointialue").get_tag("amenity") == "clinic"
    assert (
        parsed(spider, channel("Helsingin Yhteiskoulu"), "Keski-Suomen hyvinvointialue").get_tag("amenity") == "clinic"
    )
    # Wards cap rescue at clinic: hospital ontology doesn't outrank.
    ch = channel("Raaseporin TK vuodeosasto")
    ch["services"] = [{"service": {"name": "Perustason osastohoito"}}]
    ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": "sairaalat"}]}]
    assert parsed(spider, ch).get_tag("amenity") == "clinic"
    # Beach ontology on a sand pit files a beach.
    ch = channel("Hakolan hiekkamonttu")
    ch["services"] = [{"service": {"name": "Vesiliikunta"}}]
    ch["ontologyTerms"] = [
        {"name": [{"language": "fi", "value": v}]} for v in ("uimakoulut", "uimarannat", "uimavesi", "uinti")
    ]
    assert parsed(spider, ch)["extras"].get("natural") == "beach"


def test_rescue_place_beats_desk_and_upgrades():
    # A care home with a customer-service desk still files by place.
    spider = make_spider()
    ch = channel("Maya", descriptions=[{"language": "fi", "value": "Ikääntyvien asumispalveluyksikkö"}])
    ch["services"] = [{"service": {"name": "Asiakaspalvelu"}}]
    assert spider._resolve_fallback_category(Feature(), ch) == Categories.ASSISTED_LIVING
    # Psychiatric outpatient units are clinics; urgent-care desks are urgent.
    ch = channel(
        "Tays Hallituskatu",
        descriptions=[{"language": "fi", "value": "Tays Hallituskatu on psykiatrisen avohoidon toimipiste"}],
    )
    assert spider._resolve_fallback_category(Feature(), ch) == Categories.CLINIC
    ch = channel(
        "Päivystyksellinen kuulokojehuolto",
        descriptions=[
            {"language": "fi", "value": "Hoidamme päivystyksellisessä kuulokojehuollossa kiireelliset tapaukset"}
        ],
    )
    assert spider._resolve_fallback_category(Feature(), ch) == Categories.CLINIC_URGENT
    # Bare social + supported-housing wording upgrades; nothing else does.
    ch = channel("X", descriptions=[{"language": "fi", "value": "Tuettua asumista tarjolla"}])
    item = Feature()
    item["extras"]["amenity"] = "social_facility"
    assert spider._maybe_upgrade_housing(item, ch, Categories.SOCIAL_FACILITY) == Categories.ASSISTED_LIVING
    assert item["extras"]["social_facility"] == "assisted_living"
    assert spider.crawler.stats.get_value("ptv_fi/category/supported_housing_upgrade") == 1
    bare = Feature()
    bare["extras"]["amenity"] = "social_facility"
    bare["extras"]["social_facility"] = "group_home"
    ch_kept = channel("X", descriptions=[{"language": "fi", "value": "tuettua asumista"}])
    assert spider._maybe_upgrade_housing(bare, ch_kept, Categories.SOCIAL_FACILITY) == Categories.SOCIAL_FACILITY
    assert bare["extras"]["social_facility"] == "group_home"
    assert spider.crawler.stats.get_value("ptv_fi/category/supported_housing_kept") == 1
    for pinned in (Categories.OFFICE_GOVERNMENT, Categories.CLINIC, Categories.SCHOOL):
        assert spider._maybe_upgrade_housing(Feature(), ch, pinned) == pinned


def test_group_activity_guard_and_table_shadow():
    # The group IS the institution for facility prefixes; bare activity
    # groups stay generic and the orchestra is not an activity.
    spider = make_spider()
    assert not spider._is_group_activity("helsingin kaupunginorkesteri")
    assert cat(spider, "Terveyskeskusryhmä")[0] == Categories.CLINIC


def test_utility_building_venues_name_the_poi():
    # "... / Huoltorakennus" with Urheilukentät services: the venue field
    # names and types the POI, never the utility building.
    spider = make_spider()
    ch = channel("Eläintarhan urheilukenttä / Huoltorakennus 3")
    ch["services"] = [{"service": {"name": "Urheilukentät"}}]
    item = parsed(spider, ch)
    assert item.get_tag("leisure") == "pitch"
    assert item["name"] == "Eläintarhan urheilukenttä"
    assert spider._carve_room_tail("Alue / Huoltorakennus") == (None, None)


# ---- End to end: venues, operators, located_in -----------------------------------


def test_operator_tail_venues_drop():
    # Association tails are no venue; venue+operator tails keep the venue
    # located and take only the association half as operator.
    spider = make_spider()
    item = parsed(spider, channel("Löytöeläimet Eura, Säkylä ja Rauma / Eläinten hyväksi EHY ry"))
    assert item["name"] == "Löytöeläimet Eura, Säkylä ja Rauma"
    assert item.get("located_in") is None
    assert item["extras"]["amenity"] == "animal_shelter"
    item = parsed(spider, channel("Iltapäivätoiminta / Tapanilan urheilukeskus, Tapanilan Erä ry"))
    assert item["located_in"] == "Tapanilan urheilukeskus"
    assert item["operator"] == "Tapanilan Erä ry"
    item = parsed(spider, channel("Iltapäivätoiminta / Päiväkoti Gan Jeladim, Helsingin juutalainen seurakunta"))
    assert item["located_in"] == "Päiväkoti Gan Jeladim"
    assert item["operator"] == "Helsingin juutalainen seurakunta"
    assert (item.get("extras") or {}).get("operator:type") == "religious"
    item = parsed(spider, channel("Imatra Bowling Center / Imatran keilahalli Oy"), "Imatran kaupunki")
    assert item["name"] == "Imatra Bowling Center"
    assert item.get("located_in") is None
    assert item["operator"] == "Imatran keilahalli Oy"
    assert item["extras"].get("operator:type") == "private"


def test_venue_hosts_locate_end_to_end():
    spider = make_spider()
    item = parsed(spider, channel("Hansakallion ympärivuorokautinen asumispalvelu (Masto, Styyrpuuri,Vantti)"))
    assert item["name"] == "Hansakallion ympärivuorokautinen asumispalvelu"
    assert item["located_in"] == "Masto, Styyrpuuri, Vantti"
    assert (
        item["extras"]["official_name"] == "Hansakallion ympärivuorokautinen asumispalvelu (Masto, Styyrpuuri,Vantti)"
    )
    item = parsed(spider, channel("Riihikoti, Villava, ikäihmisten asumispalvelut", office="RIIHIMÄKI"))
    assert item["name"] == "Ikäihmisten asumispalvelut"
    assert item["located_in"] == "Riihikoti, Villava"
    item = parsed(
        spider, channel("Teuvolan vammaisten asumispalvelut, tilapäishoito ja loma-ajanhoito, Forssa", office="FORSSA")
    )
    assert item["name"] == "Teuvolan vammaisten asumispalvelut"
    assert item.get("located_in") is None
    item = parsed(spider, channel("Lempeä selkäjooga-ryhmä, Veittijärven koulu -palvelun järjestämispaikka"))
    assert item["name"] == "Lempeä selkäjooga-ryhmä"
    assert item["located_in"] == "Veittijärven koulu"
    assert item.get_tag("amenity") == "yes"
    item = parsed(spider, channel("Kivari, Riihimäki, Vammaisten asumispalvelut", office="RIIHIMÄKI"))
    assert item["name"] == "Vammaisten asumispalvelut"
    assert item["located_in"] == "Kivari"
    item = parsed(
        spider,
        channel(
            "Ikifit Oy, hyvinvointikeskus Keinupuisto/Hilpi, Hämeenlinna, yhteisöllisen asumisen ostopalvelut",
            office="HÄMEENLINNA",
        ),
    )
    assert item["name"] == "Ikifit Oy, hyvinvointikeskus Keinupuisto/Hilpi"
    assert item.get("located_in") is None
    item = parsed(spider, channel("Jumppa / Lahti", road="Katu", street_number="1", office="LAHTI"), "Lahden kaupunki")
    assert item.get("located_in") is None
    assert item["city"] == "Lahti"


def test_service_names_at_hosts_end_to_end():
    spider = make_spider()
    item = parsed(spider, channel("Äänekosken poliisiasema, lupapalvelut", office="ÄÄNEKOSKI"))
    assert item["name"] == "Lupapalvelut"
    assert item["located_in"] == "Äänekosken poliisiasema"
    assert item.get_tag("office") == "government"
    item = parsed(
        spider, channel("Lastentautien poliklinikka, Forssan sairaala", office="FORSSA"), "Kanta-Hämeen hyvinvointialue"
    )
    assert item["name"] == "Lastentautien poliklinikka"
    assert item["located_in"] == "Forssan sairaala"
    assert item.get("branch") is None
    item = parsed(
        spider,
        channel("Rovastinkankaan koulun opiskeluhuolto, Orivesi", office="ORIVESI"),
        "Pirkanmaan hyvinvointialue",
    )
    assert item["name"] == "Opiskeluhuolto"
    assert item["located_in"] == "Rovastinkankaan koulu"
    assert item["extras"]["official_name"] == "Rovastinkankaan koulun opiskeluhuolto, Orivesi"
    item = parsed(spider, channel("Ite ja yhessä - toiminta/Kyläryhmä -palvelun järjestämispaikka, Virolahti 2"))
    assert item["located_in"] == "Kyläryhmä"
    assert spider._clean_located_value("Kyläryhmä -palvelun järjestämispaikka, Virolahti 2", None) == "Kyläryhmä"


def test_names_capitalize_and_keep_compounds():
    spider = make_spider()
    assert parsed(spider, channel("vaatelahjoitus"), "Verso ry")["name"] == "Vaatelahjoitus"
    item = parsed(
        spider,
        channel("Kokemäen äitiysneuvola, perhekeskus Suvituuli", office="KOKEMÄKI"),
        "Satakunnan hyvinvointialue",
    )
    assert item["located_in"] == "Perhekeskus Suvituuli"
    assert parsed(spider, channel("Pertunmaa-talo"))["name"] == "Pertunmaa-talo"
    assert parsed(spider, channel("Kajaanin Vesi -liikelaitos"))["name"] == "Kajaanin Vesi -liikelaitos"
    assert parsed(spider, channel("Kajaanin Vesi -liikelaitos")).get_tag("office") == "company"
    item = parsed(spider, channel("Näe hyvä mussa -leirit lapsille -palvelun järjestämispaikka, 1"))
    assert item["name"] == "Näe hyvä mussa -leirit lapsille"
    assert item["extras"]["official_name"] == "Näe hyvä mussa -leirit lapsille -palvelun järjestämispaikka, 1"
    item = parsed(spider, channel("Kuntosali yhdistyksen jäsenille -palvelun järjestämispaikka"))
    assert item["name"] == "Kuntosali yhdistyksen jäsenille"
    item = parsed(spider, channel("Rikos -ja riita-asioiden sovittelua -palvelun järjestämispaikka"))
    assert item["name"] == "Rikos -ja riita-asioiden sovittelua"
    assert parsed(spider, channel("Språkcafé på svenska i Ode bibliotek - Syksy 2026 -palvelun järjestämispaikka"))[
        "name"
    ] == ("Språkcafé på svenska i Ode bibliotek - Syksy 2026")


def test_ostopalvelut_and_coverage_tails_end_to_end():
    # Purchased-service qualifiers arrange the service, never the place;
    # municipality segments repeat the city field, never locate.
    spider = make_spider()
    ch = channel("Attendo Puistomäki, Hämeenlinna, yhteisöllisen asumisen ostopalvelut", office="Hämeenlinna")
    ch["services"] = [{"service": {"name": "Sosiaalihuoltolain mukainen yhteisöllinen asuminen"}}]
    item = parsed(spider, ch, "Kanta-Hämeen hyvinvointialue")
    assert item.get_tag("amenity") == "social_facility"
    assert item.get("name") == "Attendo Puistomäki"
    assert item["extras"].get("leisure") is None
    ch = channel(
        "Ikifit Oy, hyvinvointikoti Jukola/Hannes, Hämeenlinna, yhteisöllisen asumisen ostopalvelut",
        office="Hämeenlinna",
    )
    assert parsed(spider, ch, "Kanta-Hämeen hyvinvointialue").get("located_in") == "Hannes"


def test_dash_city_and_located_hygiene():
    spider = make_spider()
    ch = channel(
        "Kansantanssin aikuisten ryhmä Vilhot ja Vienot - Hollola -palvelun järjestämispaikka",
        road="Katu",
        street_number="1",
        office="HOLLOLA",
    )
    assert parsed(spider, ch)["name"] == "Kansantanssin aikuisten ryhmä Vilhot ja Vienot"


def test_daycare_ground_and_room_splits():
    # Daycare yards read like schoolyards with no venue split either way.
    spider = make_spider()
    for full in ("Lapijoen päiväkodin lähiliikuntapaikka", "Ilolan koulun lähiliikuntapaikka"):
        assert spider._split_name(full, None) == (full, None, None)


def test_unmapped_and_opaque_stays_generic():
    spider = make_spider()
    assert parsed(spider, channel("Tukipuu")).get_tag("amenity") == "yes"
    ch = channel("Söderkullan kartano")
    ch["services"] = [{"service": {"name": "Matonpesupaikat"}}]
    assert parsed(spider, ch).get_tag("amenity") == "yes"


def test_senior_housing_carries_for_senior():
    spider = make_spider()
    item = parsed(spider, channel("Ikäihmisten asumispalvelut"))
    assert item.get_tag("amenity") == "social_facility"
    assert item["extras"].get("social_facility:for") == "senior"
    item = parsed(spider, channel("Bromarv pensionärsbostäder"))
    assert item.get_tag("amenity") == "social_facility"
    assert item["extras"].get("social_facility:for") == "senior"


def test_city_dash_prefix_drops():
    # "Jämsä – päivätoimintaa kuntoutujille": the city prefix drops, the
    # full signed form survives in official_name.
    item = Feature()
    make_spider()._apply_naming(
        item,
        {"fi": "Jämsä – päivätoimintaa kuntoutujille"},
        "Jämsä – päivätoimintaa kuntoutujille",
        "Jämsä",
    )
    assert item["name"] == "Päivätoimintaa kuntoutujille"
    assert item["extras"]["official_name"] == "Jämsä – päivätoimintaa kuntoutujille"


def test_source_and_check_date_pins():  # Every channel carries its stable Suomi.fi page and update date.
    ch = channel("Vojakkalan uimapaikka, Kaartjärvi")
    ch["modified"] = "2026-10-08T08:00:00.000000"
    item = parsed(make_spider(), ch)
    assert item["extras"]["source"] == (
        "https://www.suomi.fi/palvelut/palvelupiste/11111111-1111-4111-8111-111111111111"
    )
    assert item["extras"]["check_date"] == "2026-10-08"


# ---- Operators ----------------------------------------------------------------------
# Explicit-in-name beats the city maintainer; associations, companies and
# parishes mark operator:type; the Kela agency survives maintainers.


@pytest.mark.parametrize(
    "org,want",
    [
        ("Teatterikoulu ILMI Ö.", True),
        ("Rikosuhripäivystys - RIKU", True),
        ("Eerikinkatu 1", False),
        ("Kuopion Nuorten Naisten Kristillinen Yhdistys (Kuopion NNKY)", True),
        ("Pohjanmaan Syöpäyhdistys (Ostrobotnia Cancer organisation)", True),
        ("Turun ja Kaarinan seurakuntayhtymä", False),
        ("Kirkkonummen suomalainen seurakunta", False),
        ("Helsingin vapaaseurakunta ry", True),
        ("Hollolan Nuorisoseura", True),
        ("Joensuun bridgekerho ry", True),
        ("Tampereen seurakunnat", False),
        ("Palvelualojen Työttömyyskassa", True),
        ("Suomen Punainen Risti Kuopion osasto", True),
        ("SANL ry / Luetaan yhdessä -verkosto", True),
        ("Keravan kansantanssijat", True),
        ("Attendo", True),
        ("Helsingin kaupunki", False),
        ("Satakunnan Sininauha", True),
        ("Yhdistys (NNKY)", True),
    ],
)
def test_private_org_markers(org, want):
    assert make_spider()._is_private_org(org) is want, org


@pytest.mark.parametrize(
    "org,want",
    [
        ("Al-Anon Keskuspalvelu r.y.", True),
        ("Barnavårdsföreningen i Finland r.f.", True),
        ("Tmi Petri Lehto", True),
        ("Derby", False),
        ("Imatran keilahalli Oy (Helsinki)", True),
        ("Daycare Daisy Oy (Ylioppilaskylä 25)", True),
        ("Musiikkipäiväkoti Sinikello (Tuureporinkatu 5 E)", False),
    ],
)
def test_operator_word_markers(org, want):
    assert make_spider()._has_operator_word(org) is want, org


def test_operator_tiers_end_to_end():
    spider = make_spider()
    # Register keepers carry no operator.
    item = Feature()
    spider._apply_operator(item, "Suomen Apteekkariliitto")
    assert "operator" not in item
    assert spider.crawler.stats.get_value("ptv_fi/operator/register_keeper") == 1
    # Municipalities carry Wikidata; the Kela agency beats maintainers.
    item = Feature()
    spider._apply_operator(item, "Helsingin kaupunki")
    assert item["operator"] == "Helsingin kaupunki"
    assert item["operator_wikidata"] == "Q1757"
    item = Feature()
    item["operator"] = "Kela"
    spider._apply_operator(item, "Kokemäen kaupunki")
    assert item["operator"] == "Kela"
    # Branch-agency tags apply at the branch pass (the org join
    # early-returns behind provisional operators): Kela carries its QID.
    assert item["operator_wikidata"] == "Q3557354"
    assert spider.crawler.stats.get_value("ptv_fi/operator/branch_agency") == 1
    # A provisional association demotion never survives a public record.
    item = Feature()
    item["operator"] = "YSTI ry"
    item["extras"]["office"] = "association"
    spider._apply_operator(item, "Yhdessä Selviytymisen Tuki YSTI ry", "Organization")
    assert item.get("operator") == "Yhdessä Selviytymisen Tuki YSTI ry"
    assert "office" not in (item.get("extras") or {})
    # Associations demote to association desks with private type.
    item = Feature()
    spider._apply_operator(item, "Olka ry")
    assert item["operator"] == "Olka ry"
    assert item["extras"]["operator:type"] == "private"
    item = Feature()
    apply_category(Categories.OFFICE_GOVERNMENT, item)
    spider._apply_operator(item, "Pirkanmaan Sydänyhdistys ry")
    assert item["extras"]["office"] == "association"
    assert item["extras"]["operator:type"] == "private"
    # Parishes are public-law bodies, never associations.
    item = Feature()
    apply_category(Categories.OFFICE_GOVERNMENT, item)
    spider._apply_operator(item, "Parikkalan seurakunta")
    assert item["operator"] == "Parikkalan seurakunta"
    assert item["extras"].get("office") == "government"
    assert item["extras"].get("operator:type") == "religious"
    ch = channel("Kansantanssin aikuisten ryhmä Vilhot ja Vienot - Hollola")
    assert parsed(make_spider(), ch, org_name="Hollolan Nuorisoseura")["extras"].get("operator:type") == "private"


def test_operator_names_and_brands():
    spider = make_spider()
    # Chain brand heads operate over purchaser cities.
    for name, brand in (("Pilke Kilonkallio", "Pilke"), ("Norlandia Kärry", "Norlandia")):
        item = parsed(spider, channel(name), "Espoon kaupunki")
        assert item["operator"] == brand
        assert item["extras"].get("operator:type") == "private"
    # Mid-name chain brands and dropped slash-head operators still operate.
    item = parsed(
        spider, channel("Päiväkoti Pilke Äppelbo daghem"), "Turun kaupunki, Kasvatuksen ja koulutuksen toimiala"
    )
    assert item["operator"] == "Pilke"
    item = parsed(spider, channel("Pilke päiväkodit Oy/ Veturi (Bastioninkatu 4)"), "Turun kaupunki")
    assert item.get("name") == "Veturi"
    assert item.get("operator") == "Pilke päiväkodit Oy"
    assert item["extras"].get("operator:type") == "private"
    item = parsed(
        spider, channel("Pilke päiväkodit Oy/ Päiväkoti Pilke Äppelbo daghem (Stålarminkatu 36)"), "Turun kaupunki"
    )
    assert item.get("operator") == "Pilke"
    # Record-proven companies are private; liikelaitos stays out.
    item = parsed(spider, channel("Palvelupiste"), None)
    spider._apply_operator(item, "Amuri Hoiva", "Company")
    assert item["extras"].get("operator:type") == "private"
    item2 = parsed(spider, channel("Palvelupiste"), None)
    spider._apply_operator(item2, "Oulun Vesi -liikelaitos", "Company")
    assert item2["extras"].get("operator:type") is None
    # Signed short forms yield to the fuller joined record.
    item = parsed(spider, channel("Ysti ry/ Toimela"), None)
    spider._apply_operator(item, "Yhdessä Selviytymisen Tuki YSTI ry", "Organization")
    assert item.get("operator") == "Yhdessä Selviytymisen Tuki YSTI ry"
    # Last-segment companies operate; activity halves never relocate.
    item = parsed(
        spider,
        channel("Iltapäivätoiminta / Taivallahden peruskoulu, Demo iltapäiväkerho / Jamkicks Oy"),
        "Helsingin kaupunki",
    )
    assert item.get("operator") == "Jamkicks Oy"
    assert item["extras"].get("operator:type") == "private"
    item = parsed(
        spider,
        channel("Iltapäivätoiminta / Vattuniemen ala-aste / Linguajoy Language Club, Linguajoy Kielikerhot Oy"),
        "Helsingin kaupunki",
    )
    assert item.get("located_in") == "Vattuniemen ala-aste"
    assert item.get("operator") == "Linguajoy Kielikerhot Oy"
    # Commercial forms keep government filings; parish slash-tails mark religious.
    tmi_item = parsed(spider, channel("Palvelupiste / Tmi Petri Lehto"), "Oulun kaupunki")
    assert tmi_item.get("operator") == "Tmi Petri Lehto"
    assert tmi_item["extras"].get("operator:type") == "private"
    assert tmi_item.get_tag("office") == "government"
    parish_item = parsed(spider, channel("Päiväkerho / Helsingin seurakunta"), "Helsingin kaupunki")
    assert parish_item.get("operator") == "Helsingin seurakunta"
    assert parish_item["extras"].get("operator:type") == "religious"
    # Patient-association desks demote to office=association.
    item = parsed(spider, channel("Luustoinfo osteoporoosia sairastaville / Lahti"), org_name="Suomen Luustoliitto ry")
    assert item["extras"].get("office") == "association"
    item = parsed(spider, channel("X"), "Pohjois-Savon Muisti ry / Pohjois-Savon Muistiluotsi")
    assert item["operator"] == "Pohjois-Savon Muisti ry"
    # Deparened companies read like bare Oy.
    item = parsed(spider, channel("Palvelupiste"), "Foo Oy (Espoo)")
    assert item.get("operator") == "Foo Oy (Espoo)"
    assert item["extras"].get("operator:type") == "private"
    assert item["extras"].get("office") == "government"
    # Brand suffixes and company markers: explicit-in-name wins.
    item = parsed(spider, channel("TestPlace"), "Pohjois-Karjalan hyvinvointialue – Siun sote")
    assert item["operator"] == "Pohjois-Karjalan hyvinvointialue"
    assert item["extras"].get("operator:type") is None
    item = parsed(spider, channel("TestPlace"), "Brottsofferjouren - RIKU")
    assert item["operator"] == "Brottsofferjouren"
    assert item["extras"].get("operator:type") == "private"
    item = parsed(spider, channel("TestPlace"), "FinFami - Uusimaa ry")
    assert item["operator"] == "FinFami - Uusimaa ry"
    assert item["extras"].get("operator:type") == "private"
    # Foundations without markers are private by record shape.
    assert (
        parsed(spider, channel("Viherlaakson asumispalveluyksikkö", org="Mente säätiö sr"), "Mente säätiö sr")[
            "extras"
        ].get("operator:type")
        == "private"
    )


def test_kela_names_the_provider():
    spider = make_spider()
    item = parsed(spider, channel("Kokemäen Asiointipiste/Kela"), "Kokemäen kaupunki")
    assert item["name"] == "Kokemäen Asiointipiste"
    assert item["operator"] == "Kela"
    assert item["extras"]["official_name"] == "Kokemäen Asiointipiste/Kela"
    assert item["city"] == "Helsinki"
    assert parsed(spider, channel("Kelan asiointipiste Lapinlahdella"), "Lapinlahden kunta")["operator"] == "Kela"


def test_branches_file_or_drop():
    spider = make_spider()
    # Non-school colon desks file the branch and keep the name.
    item = parsed(spider, channel("Rakennusvalvontatoimisto: Sampola"))
    assert item["branch"] == "Sampola"
    assert item["name"] == "Rakennusvalvontatoimisto: Sampola"
    # Schools never branch; city-repeat branches are not branches.
    item = parsed(
        spider, channel("Tampereen seudun työväenopiston toimisto: Sampola", office="TAMPERE"), "Tampereen kaupunki"
    )
    assert item.get("branch") is None
    item = parsed(spider, channel("Stadin ammattiopisto, Roihupellon toimipaikka"), "Helsingin kaupunki")
    assert item.get("branch") is None
    assert item["extras"].get("official_name") is None
    item = parsed(spider, channel("Korva-, nenä- ja kurkkutautien poliklinikka"))
    assert item.get("branch") is None
    assert item["name"] == "Korva-, nenä- ja kurkkutautien poliklinikka"
    # Imaging branches: city repeats drop, unit remainders branch.
    item = parsed(spider, channel("Kuvantaminen, Pirkkala", office="PIRKKALA"), "Pirkanmaan hyvinvointialue")
    assert item["name"] == "Kuvantaminen"
    assert item.get("branch") is None
    assert item["city"] == "Pirkkala"
    item = parsed(
        spider, channel("Kuvantaminen, Pirkkala Pirkkalan röntgen", office="PIRKKALA"), "Pirkanmaan hyvinvointialue"
    )
    assert item["branch"] == "Pirkkalan röntgen"
    # Name/city duplicating branches drop with a count.
    item = parsed(spider, channel("Toimisto: Sampola"))
    item["name"] = "Sampola"
    spider._apply_branch(item, "Toimisto: Sampola", "Sampola", None, None)
    assert "branch" not in item
    spider._apply_branch(item, "Toimisto: Pöytyä", "Toimisto: Pöytyä", None, "Pöytyä")
    assert "branch" not in item
    assert spider.crawler.stats.get_value("ptv_fi/name/branch_dup_city") == 1


# ---- Contact: phones, emails, websites -------------------------------------------------


def test_contact_keep_and_drop():
    spider = make_spider()
    item = Feature()
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
    item = Feature()
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
    # Placeholder and template addresses drop or yield to real entries.
    for bad in ("etunimi.sukunimi@kalajoki.fi", "nimi.sukunimi@kunta.fi"):
        probe = Feature()
        spider._apply_contact(probe, {"emails": [{"value": bad}]})
        assert "email" not in probe, bad
    ch = channel("X")
    ch["emails"] = [{"value": "etunimi.sukunimi@soini.fi"}, {"value": "soinin.kunta@soini.fi"}]
    assert parsed(spider, ch).get("email") == "soinin.kunta@soini.fi"
    # Menu SaaS hosts never pose as websites; the next usable page wins.
    probe = Feature()
    spider._apply_contact(probe, {"webPages": [{"url": "https://menu.kaarea.fi/KaareaAromieMenus/FI/Default"}]})
    assert "website" not in probe
    ch = channel("X")
    ch["webPages"] = [{"url": "https://aromimenu.cgisaas.fi/X"}, {"url": "https://www.kirjasto.fi/"}]
    assert parsed(spider, ch).get("website") == "https://www.kirjasto.fi/"
    ch = channel("Kotoutumispalvelut / Vaasan kaupungin hyvinvointipalvelut", office="Vaasa")
    ch["webPages"] = [{"url": "http://www.finlex.fi/fi/laki/ajantasa/2010/20101386"}]
    assert parsed(spider, ch, "Vaasan kaupunki").get("website") is None
    # The city switchboard serves 145 rows: never a direct contact.
    probe = Feature()
    spider._apply_contact(probe, {"phoneNumbers": [{"prefixNumber": "+358", "number": "983911"}]})
    assert probe.get("phone") is None
    # Canonical shapes (+358, trunk, bare) all hit the same set.
    assert spider._canonical_phone_digits("+358 9 81621") == "981621"
    assert spider._canonical_phone_digits("09 81621") == "981621"
    assert spider._canonical_phone_digits("981621") == "981621"
    # Audited centrals drop in every feed shape; ordinary numbers survive.
    for digits in ("931022111", "983922242", "295419800", "116117", "94711", "2330000"):
        probe = Feature()
        spider._apply_contact(probe, {"phoneNumbers": [{"prefixNumber": "+358", "number": digits}]})
        assert probe.get("phone") is None, digits
    # Round-24 fallback findings: shared Ulosotto lines and bare 112 drop.
    for digits in ("295658807", "295658801"):
        probe = Feature()
        spider._apply_contact(probe, {"phoneNumbers": [{"prefixNumber": "+358", "number": digits}]})
        assert probe.get("phone") is None, digits
    probe = Feature()
    spider._apply_contact(probe, {"phoneNumbers": [{"prefixNumber": "", "number": "112"}]})
    assert probe.get("phone") is None
    probe = Feature()
    spider._apply_contact(probe, {"phoneNumbers": [{"prefixNumber": "", "number": "09 4711"}]})
    assert probe.get("phone") is None
    probe = Feature()
    spider._apply_contact(probe, {"phoneNumbers": [{"prefixNumber": "", "number": "116117"}]})
    assert probe.get("phone") is None
    # A generic first line yields to a real second line.
    probe = Feature()
    spider._apply_contact(
        probe,
        {
            "phoneNumbers": [
                {"prefixNumber": "+358", "number": "931022111"},
                {"prefixNumber": "", "number": "040 123 4567"},
            ]
        },
    )
    assert probe.get("phone") == "+358 40 1234567"


def test_fax_lines_yield_to_voice():
    spider = make_spider()
    ch = channel("Konsertti- ja kongressitalo Mikaeli")
    ch["phoneNumbers"] = [
        {"type": "Fax", "number": "+358 15 362 757", "prefixNumber": ""},
        {"type": "Phone", "number": "+358 15 336 080", "prefixNumber": ""},
    ]
    assert parsed(spider, ch).get("phone") == "+358 15336080"
    ch["phoneNumbers"] = [None, {}, {"type": "Phone", "number": "040 123 4567", "prefixNumber": ""}]
    assert parsed(spider, ch).get("phone") == "+358 40 1234567"


def test_login_and_mail_urls_never_win():
    spider = make_spider()
    for bad in (
        "https://hushag-sso.hus.fi/haglogin/idp-discovery.jsp",
        "https://aromimenu.cgisaas.fi/X",
        "https://tyollisyyskokeilu@raahe.fi/",
        "https://eur06.safelinks.protection.outlook.com/?url=x",
    ):
        assert spider.LOGIN_URL_RE.search(bad), bad
    for good in (
        "https://www.kirjasto.fi/",
        "https://biologinenmuseo.fi/",
        "https://www.hus.fi/potilaalle/sairaalat-ja-toimipisteet/neurologinen-kuntoutusosasto-2/",
        "https://www.hel.fi/fi/sosiaali-ja-terveyspalvelut/vammaispalvelut/sosiaalityo/",
    ):
        assert not spider.LOGIN_URL_RE.search(good), good


@pytest.mark.parametrize(
    "raw,want",
    [
        ("094711", "+358 9 4711"),
        ("0206156605", "+358 206156605"),
        ("+358 0503273734", "+358 50 3273734"),
        ("+358 358447851490", "+358 44 7851490"),
        ("+358 49460076255", None),
        ("116006", "116006"),
        ("null", None),
        ("400395234", "+358 40 0395234"),
        ("4578757018", None),
        ("358 17499111", "+358 17499111"),
        ("116117", "116117"),
        ("+359 447301262", "+358 44 7301262"),
        ("+358 358123456", "+358 1 23456"),
        ("00358 9 1234567", "+358 91234567"),
        ("358912345", "+358 9 12345"),
    ],
)
def test_phone_normalize(raw, want):
    assert make_spider()._normalize_phone(raw) == want, raw


# ---- Translations ------------------------------------------------------------------------
# name:sv/name:en render only the applied name, feed-verbatim: venue,
# operator, city and street tails strip; truncated Finnish copies drop.


def test_translations_render_the_applied_name():
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
    item = parsed(
        spider,
        channel(
            "Sodanajan naisen muistomerkki",
            en="Sodanajan naisen muistomerkki / Memorial to Women in Times of War",
            sv="Den krigstida kvinnans minnesmärke",
        ),
    )
    assert item["extras"].get("name:en") == "Memorial to Women in Times of War"
    assert item["extras"].get("name:sv") == "Den krigstida kvinnans minnesmärke"
    item = parsed(
        spider,
        channel(
            "Moduli / Rakentajaveistos", en="Moduli (Rakentajaveistos) / The Module", sv="Modul / Byggarnas minnesmärke"
        ),
    )
    assert item["name"] == "Moduli / Rakentajaveistos"
    assert item.get("located_in") is None
    item = parsed(spider, channel("Ristikko", sv="Korsverk (Ristikko)", en="Crosses"))
    assert item["extras"].get("name:sv") == "Korsverk"
    assert item["extras"].get("name:en") == "Crosses"
    item = parsed(
        spider,
        channel(
            "Filosofia, Lääketiede, Teologia ja Juridiikka",
            en="Filosofia, lääketiede.../ Philosophy, Medicine, Theology and Justice",
        ),
    )
    assert item["extras"].get("name:en") == "Philosophy, Medicine, Theology and Justice"
    item = parsed(spider, channel("Aninkaisten koulun A-sali", en="Aninkaisten koulu (Aninkainen School) Gym A"))
    assert item.get("located_in") == "Aninkaisten koulu"
    assert item["extras"].get("name:en") == "(Aninkainen School) Gym A"
    item = parsed(spider, channel("Leikkipuisto Jakomäki / Hiekkakenttä", en="Leikkipuisto Jakomäki"))
    assert item.get("located_in") == "Leikkipuisto Jakomäki"
    assert "name:en" not in (item.get("extras") or {})
    item = parsed(
        spider,
        channel(
            "Steinergymnasiet (Rudolf Steinerskolan i Helsingfors)",
            sv="Steinergymnasiet (Rudolf Steinerskolan i Helsingfors)",
            en="Steinergymnasiet (Rudolf Steinerskolan i Helsingfors)",
        ),
    )
    assert item["name"] == "Steinergymnasiet"
    assert "name:sv" not in item["extras"]
    assert "name:en" not in item["extras"]


def test_translation_helpers_strip_venues_and_copies():
    spider = make_spider()
    assert (
        spider._split_bilingual(
            "After-school activities / Helsinki Christian School / Association of X",
            "Iltapäivätoiminta",
            "Iltapäivätoiminta / Helsingin kristillinen koulu, Yhdistys",
            "Helsingin kristillinen koulu",
        )
        == "After-school activities"
    )
    assert (
        spider._split_bilingual(
            "Röylän koulu / Ice-skating field", "Luistelukenttä", "Röylän koulun luistelukenttä", "Röylän koulu"
        )
        == "Ice-skating field"
    )
    assert (
        spider._strip_fi_duplicates(
            "Hjälpmedelsutlåningen, Reso, Rusko", "Apuvälinelainaamo", "Apuvälinelainaamo, Raisio, Rusko", None
        )
        == "Hjälpmedelsutlåningen"
    )
    assert (
        spider._strip_fi_duplicates(
            "Röylän koulu skridskobana", "Luistelukenttä", "Röylän koulun luistelukenttä", "Röylän koulu"
        )
        == "skridskobana"
    )
    assert (
        spider._split_bilingual(
            "After-school activities / Helsinki Christian School",
            "Iltapäivätoiminta",
            "Iltapäivätoiminta / Helsingin kristillinen koulu",
            "Helsingin kristillinen koulu",
        )
        == "After-school activities"
    )
    assert (
        spider._split_bilingual(
            "After-school activities / University of Helsinki",
            "Viikin normaalikoulun iltapäivätoiminta, Helsingin",
            "Iltapäivätoiminta / Viikin normaalikoulun iltapäivätoiminta, Helsingin yliopisto",
            "Iltapäivätoiminta",
        )
        == "After-school activities / University of Helsinki"
    )
    assert spider._split_translation("Simhallen - Uimahalli") == ("Uimahalli", "Simhallen")
    # Case/separator-only copies are not translations; genuine compounds stay.
    assert spider._tr_same("Vantaa Info, Korso", "Vantaa-info, Korso")
    assert spider._tr_same("hiekkakenttä", "Hiekkakenttä")
    assert not spider._tr_same("Minervaskolan", "Minerva skolan")
    assert not spider._tr_same("Riksarkivet Helsingfors", "Kansallisarkisto")
    assert spider._tr_align_venue_drop("", "X", "A / B", "C") == ""
    item = parsed(make_spider(), channel("Hiekkakenttä", en="hiekkakenttä"))
    assert "name:en" not in item["extras"]
    item = parsed(make_spider(), channel("Vantaa-info, Korso", sv="Vantaa Info, Korso", office="KORSO"))
    assert "name:sv" not in item["extras"]
    item = parsed(make_spider(), channel("Kansallisarkisto", sv="Riksarkivet Helsingfors"))
    assert item["extras"].get("name:sv") == "Riksarkivet Helsingfors"


def test_translation_city_street_and_located_tails():
    spider = make_spider()
    item = parsed(spider, channel("Sosiaalitoimisto, Kaarina", sv="Socialbyrå, S:t Karins", office="KAARINA"))
    assert item["extras"].get("name:sv") == "Socialbyrå"
    item = parsed(spider, channel("Koivukoto, Laitila", sv="Koivukoto, Letala", office="LAITILA"))
    assert item["extras"].get("name:sv") is None
    item = parsed(
        spider,
        channel(
            "Pysäköintilippuautomaatti 99, Nervanderinkatu 3, korttimaksu",
            sv="Parkeringbiljettautomat 99, Nervanderinkatu 3",
            en="Parking ticket machine, Kaisaniemenranta 2",
        ),
    )
    assert item["extras"].get("name:sv") == "Parkeringbiljettautomat 99"
    assert item["extras"].get("name:en") == "Parking ticket machine"
    ch = channel(
        "Päiväkotikeittiö, Päiväkoti Jollas",
        sv="Daghemskök, Päiväkoti Jollas",
        en="Daycare centre kitchen, Daycare Jollas",
    )
    item = parsed(spider, ch)
    assert item["extras"].get("name:sv") == "Daghemskök"
    assert item["extras"].get("name:en") == "Daycare centre kitchen"
    assert item.get("located_in") == "Päiväkoti Jollas"
    item = parsed(spider, channel("Oskarinpuisto / Lentopallokenttä", sv="Oskariparken / Volleybollplan"))
    assert item["extras"].get("name:sv") == "Volleybollplan"
    item = parsed(
        spider, channel("Bylandet / Ulkoilusaari", sv="Bylandet / Utfärdsholme", en="Bylandet / Recreational island")
    )
    assert item["extras"].get("name:sv") is None
    assert item["extras"].get("name:en") is None
    assert item.get("located_in") is None
    # Bare-slash twins keep both sides; only spaced twins follow the split.
    item = parsed(spider, channel("Lauttasaaren silta/ Kaapelitehdas", sv="Drumsö bro/ Kabelfabriken"))
    assert item["extras"].get("name:sv") == "Drumsö bro/ Kabelfabriken"


def test_translation_descriptor_and_address_parens_drop():
    spider = make_spider()
    ch = channel("Päiväkoti Lyyra")
    ch["serviceChannelNames"] = [
        {"language": "fi", "value": "Päiväkoti Lyyra", "type": "Name"},
        {"language": "en", "value": "Päiväkoti Lyyra (private ECEC centre)", "type": "Name"},
    ]
    ch["displayNameType"] = [{"type": "Name", "language": "en"}]
    assert parsed(spider, ch, "Rovaniemen kaupunki")["extras"].get("name:en") is None
    ch = channel("Haritun päiväkoti (Kymenlaaksonkuja 4)")
    ch["serviceChannelNames"].append({"language": "sv", "value": "Dagvårdsenheten i Harittu (Kymmenedalsgränden 4)"})
    item = parsed(spider, ch, "Turun kaupunki")
    assert item.get("name") == "Haritun päiväkoti"
    assert item["extras"].get("name:sv") == "Dagvårdsenheten i Harittu"


def test_name_selection_prefers_parallel_forms():
    spider = make_spider()
    ch = channel("Kotoutumispalvelut / Vaasan kaupungin hyvinvointipalvelut")
    ch["serviceChannelNames"] = [
        {"language": "fi", "value": "Kotoutumispalvelut / Vaasan kaupungin hyvinvointipalvelut"},
        {"language": "sv", "value": "Integrationstjänster"},
        {"language": "sv", "value": "Integrationsservice / Vasa stad Välfärdstjänster"},
    ]
    assert spider._names(ch)["sv"] == "Integrationsservice / Vasa stad Välfärdstjänster"
    ch = channel("Kotoutumispalvelut / Vaasan kaupungin hyvinvointipalvelut", office="Vaasa")
    ch["serviceChannelNames"] = [
        {"language": "fi", "value": "Kotoutumispalvelut / Vaasan kaupungin hyvinvointipalvelut"},
        {"language": "sv", "value": "Integrationstjänster"},
        {"language": "sv", "value": "Integrationsservice / Vasa stad Välfärdstjänster"},
        {"language": "en", "value": "Integration services / City of Vaasa"},
    ]
    ch["displayNameType"] = [{"type": "Name", "language": "en"}]
    ch["webPages"] = [{"url": "http://www.finlex.fi/fi/laki/ajantasa/2010/20101386"}]
    item = parsed(spider, ch, "Vaasan kaupunki")
    assert item.get("name") == "Vaasan kaupungin hyvinvointipalvelut"
    assert item.get("located_in") == "Kotoutumispalvelut"
    assert item["extras"].get("name:sv") == "Vasa stad Välfärdstjänster"
    assert item["extras"].get("name:en") is None
    assert item.get("website") is None
    # Official Name beats AlternativeName; placeholders fall back.
    ch = channel("Talaskangas")
    ch["serviceChannelNames"] = [
        {"language": "fi", "value": "Talaskangas", "type": "AlternativeName"},
        {"language": "fi", "value": "Talaskankaan retkeilyreitti", "type": "Name"},
    ]
    ch["displayNameType"] = [{"type": "Name", "language": "fi"}]
    assert spider._names(ch)["fi"] == "Talaskankaan retkeilyreitti"
    names = spider._names(
        {
            "serviceChannelNames": [
                {"language": "sv", "value": "Kontaktuppgifter", "type": "Name"},
                {"language": "sv", "value": "AMS", "type": "AlternativeName"},
            ]
        }
    )
    assert names.get("sv") == "AMS"


# ---- Hours ---------------------------------------------------------------------------------


def _spans(open_from, open_to):
    return [
        {"dayFrom": d, "dayTo": "", "from": open_from, "to": open_to}
        for d in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
    ]


def test_hours_union_skips_phone_only():
    # Nurse/counsellor/psychologist timetables union; phone-only sets skip.
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
    spider2 = make_spider()
    oh = spider2._hours(
        {
            "serviceHours": [
                {
                    "serviceHourType": "DaysOfTheWeek",
                    "additionalInformation": [{"value": "Puhelinaika"}],
                    "openingHour": _spans("08:00:00", "10:00:00"),
                },
                {
                    "serviceHourType": "DaysOfTheWeek",
                    "additionalInformation": [{"value": "Terveydenhoitaja"}],
                    "openingHour": _spans("08:00:00", "16:00:00"),
                },
            ]
        },
        None,
    )
    assert oh.as_opening_hours() == "Mo-Fr 08:00-16:00"
    assert spider2.crawler.stats.get_value("ptv_fi/hours/phone_only") == 1


def test_hours_dated_closed_and_always_open():
    spider = make_spider()
    dated = {
        "serviceHourType": "DaysOfTheWeek",
        "validFrom": "2027-01-01T00:00:00",
        "openingHour": [{"dayFrom": "Monday", "dayTo": "", "from": "08:00:00", "to": "16:00:00"}],
    }
    assert spider._hours({"serviceHours": [dated]}, None) is None
    assert spider.crawler.stats.get_value("ptv_fi/hours/dated") == 1
    closed = {
        "serviceHourType": "DaysOfTheWeek",
        "isClosed": True,
        "openingHour": [{"dayFrom": "Monday", "dayTo": "", "from": "", "to": ""}],
    }
    assert spider._hours({"serviceHours": [closed]}, None) is None
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
    # Closed marks lose to real spans either order; multiday marks cover ranges.
    spans = {
        "serviceHourType": "DaysOfTheWeek",
        "openingHour": [{"dayFrom": "Monday", "dayTo": "", "from": "09:00:00", "to": "11:00:00"}],
    }
    closed_mark = {
        "serviceHourType": "DaysOfTheWeek",
        "isClosed": True,
        "openingHour": [{"dayFrom": "Monday", "dayTo": ""}],
    }
    for hours in ([spans, closed_mark], [closed_mark, spans]):
        ch = channel("Avoin piste")
        ch["serviceHours"] = [dict(e) for e in hours]
        assert parsed(make_spider(), ch)["opening_hours"].as_opening_hours() == "Mo 09:00-11:00"
    ch = channel("X")
    ch["serviceHours"] = [
        {
            "serviceHourType": "DaysOfTheWeek",
            "isClosed": True,
            "openingHour": [{"dayFrom": "Monday", "dayTo": "Friday"}],
        }
    ]
    day_spans, closed_days, _ = spider._hours_collect(ch)
    assert day_spans == {}
    assert closed_days == {"Mo", "Tu", "We", "Th", "Fr"}
    # Staffed care/education is not walk-in 24/7; availability never overrides spans.
    always = {
        "serviceHours": [
            {
                "serviceHourType": "DaysOfTheWeek",
                "isAlwaysOpen": True,
                "openingHour": [{"dayFrom": "Monday", "dayTo": "Sunday", "from": "00:00:00", "to": "23:59:59"}],
            }
        ]
    }
    fresh = make_spider()
    for category in (Categories.SCHOOL, Categories.KINDERGARTEN, Categories.NURSING_HOME, Categories.SOCIAL_FACILITY):
        assert fresh._hours(always, category) is None
    assert fresh.crawler.stats.get_value("ptv_fi/hours/skipped_always_open_social") == 4
    ch2 = channel("Päivystävä piste")
    ch2["serviceHours"] = [
        {"serviceHourType": "DaysOfTheWeek", "isAlwaysOpen": True},
        {
            "serviceHourType": "DaysOfTheWeek",
            "openingHour": [{"dayFrom": "Monday", "dayTo": "", "from": "08:00:00", "to": "16:00:00"}],
        },
    ]
    assert spider._hours(ch2, None) is not None
    assert spider.crawler.stats.get_value("ptv_fi/hours/always_open_with_spans") == 1
    # Upgraded assisted-living homes skip 24/7 flags like other care.
    ch_al = channel("Onnikoti Apila")
    ch_al["services"] = [{"service": {"name": "Tuettu asuminen"}}]
    ch_al["serviceHours"] = [{"serviceHourType": "DaysOfTheWeek", "isAlwaysOpen": True, "openingHour": []}]
    al_item = parsed(spider, ch_al, "Hyvinvointialue")
    assert al_item.get("extras", {}).get("social_facility") == "assisted_living"
    assert al_item.get("opening_hours") is None


def test_hours_edge_branches_and_ranges():
    # Unknown days, bad ranges and exceptional types skip with counters;
    # overlapping spans merge; overnight and wraparound ranges render.
    spider = make_spider()
    oh = spider._hours(
        {
            "serviceHours": [
                {"serviceHourType": "Exceptional", "openingHour": _spans("08:00:00", "16:00:00")},
                {
                    "serviceHourType": "DaysOfTheWeek",
                    "openingHour": [{"dayFrom": "Funday", "dayTo": "", "from": "08:00:00", "to": "16:00:00"}],
                },
                {
                    "serviceHourType": "DaysOfTheWeek",
                    "openingHour": [{"dayFrom": "Monday", "dayTo": "", "from": "xx", "to": "16:00:00"}],
                },
                {
                    "serviceHourType": "DaysOfTheWeek",
                    "openingHour": [
                        {"dayFrom": "Monday", "dayTo": "", "from": "08:00:00", "to": "12:00:00"},
                        {"dayFrom": "Monday", "dayTo": "", "from": "10:00:00", "to": "16:00:00"},
                    ],
                },
                {
                    "serviceHourType": "OverMidnight",
                    "openingHour": [{"dayFrom": "Friday", "dayTo": "", "from": "22:00:00", "to": "06:00:00"}],
                },
            ]
        },
        None,
    )
    rendered = oh.as_opening_hours()
    assert "Mo 08:00-16:00" in rendered
    assert "22:00" in rendered
    assert spider.crawler.stats.get_value("ptv_fi/hours/unknown_day") == 1
    assert spider.crawler.stats.get_value("ptv_fi/hours/bad_range") == 1
    assert spider.crawler.stats.get_value("ptv_fi/hours/skipped_type/Exceptional") == 1
    assert spider.crawler.stats.get_value("ptv_fi/hours/merged") == 1
    ch = channel("X")
    ch["serviceHours"] = [
        {
            "serviceHourType": "DaysOfTheWeek",
            "openingHour": [{"dayFrom": "Friday", "dayTo": "Monday", "from": "12:00:00", "to": "14:00:00"}],
        }
    ]
    rendered = spider._hours(ch, None).as_opening_hours()
    assert "Fr-Su 12:00-14:00" in rendered
    assert "Mo 12:00-14:00" in rendered
    assert spider._to_minutes("25:00") is None
    assert spider._to_minutes("10:00:99") is None
    assert spider._to_minutes("08:00-12:00") is None
    assert spider._to_minutes("08:00:00") == 480


# ---- Crawl plumbing: cities, coords, gates, joins --------------------------------------
# Municipality outranks the postal town; post office is fallback only.


def test_city_src_prefers_municipality():
    spider = make_spider()
    street = {"municipality": {"name": [{"language": "fi", "value": "Seinäjoki"}]}}
    assert spider._city_src(street, {"areas": []}, "KYLÄNPÄÄ") == "Seinäjoki"
    assert (
        spider._city_src(
            {}, {"areas": [{"municipalities": [{"name": [{"language": "fi", "value": "Kuusamo"}]}]}]}, "KUUSAMO"
        )
        == "Kuusamo"
    )
    multi = {
        "areas": [
            {
                "municipalities": [
                    {"name": [{"language": "fi", "value": "Helsinki"}]},
                    {"name": [{"language": "fi", "value": "Espoo"}]},
                ]
            }
        ]
    }
    assert spider._city_src({}, multi, "HELSINKI") == "HELSINKI"
    assert make_spider()._city_src({}, {"areas": []}, "ORIVESI AS") == "ORIVESI"


def test_municipality_beats_post_office_end_to_end():
    # Postal village Kylänpää must not leak into addr:city or name splits.
    spider = make_spider()
    data = channel("Neuvonta", road="Kylänpääntie", street_number="200", postcode="60420", office="KYLÄNPÄÄ")
    data["addresses"][0]["streetAddress"]["municipality"] = {"name": [{"language": "fi", "value": "Seinäjoki"}]}
    assert parsed(spider, data, "Seinäjoen kaupunki")["city"] == "Seinäjoki"
    ch = channel("X", office="KYLÄNPÄÄ")
    ch["addresses"][0]["streetAddress"]["municipality"] = {"name": [{"language": "fi", "value": "Espoo"}]}
    assert parsed(spider, ch).get("city") == "Espoo"


def test_coords_gates_and_wgs84():
    spider = make_spider()
    base = {"latitude": "6672010", "longitude": "385128"}
    assert spider._coords({**base, "coordinateState": "NotReceived"}) is None
    assert spider._coords({**base, "coordinateState": "Failed"}) is None
    assert spider._coords({**base, "coordinateState": "Ok"}) is not None
    fresh = make_spider()
    assert fresh._coords({"latitude": "1", "longitude": "2", "coordinateState": "NotReceived"}) is None
    assert fresh._coords({"latitude": "1", "longitude": "2", "coordinateState": "Failed"}) is None
    assert fresh.crawler.stats.get_value("ptv_fi/coords/dropped_state") == 2
    # Degrees filed as TM35FIN are already WGS84.
    lon, lat = spider._coords({"latitude": "64.916102", "longitude": "25.47273", "coordinateState": "EnteredByUser"})
    assert (round(lon, 2), round(lat, 2)) == (25.47, 64.92)


def test_visit_address_and_gates():
    spider = make_spider()
    single = {"type": "Location", "subType": "Single", "streetAddress": {"a": 1}}
    multi = {"type": "Location", "subType": "Multi", "streetAddress": {"b": 2}}
    postal = {"type": "Postal", "subType": "Single", "streetAddress": {"c": 3}}
    assert spider._visit_address({"addresses": [postal, multi, single]}) == single
    ch = channel("X")
    ch["addresses"] = [postal]
    assert spider.parse_channel(ch) is None
    assert spider.crawler.stats.get_value("ptv_fi/dropped/postal_only") == 1
    # Register rows without a real visit place never parse.
    assert spider.parse_channel(channel("X", office="TUNTEMATON")) is None
    assert spider.crawler.stats.get_value("ptv_fi/dropped/non_place/mobile_address") == 1
    # Id-less detail rows drop with a count, never KeyError.
    ch = channel("X")
    del ch["id"]
    assert spider.parse_channel(ch) is None
    assert spider.crawler.stats.get_value("ptv_fi/dropped/no_id") == 1
    # Mobile/bookmobile/test/crosswalk/track names never become POIs.
    assert spider._is_dropped_name("Etsivä yksikkö") == "non_place/mobile"
    assert spider._is_dropped_name("Kirjastoauto Keskusta") == "non_place/bookmobile"
    assert spider._is_dropped_name("Kuvan testipiste") == "non_place/test_data"
    assert spider._is_dropped_name("Mannerheimintien suojatie") == "non_place/crosswalk"
    assert spider._is_dropped_name("Pirkkolan kuntorata") == "non_place/track"
    # Venue heads inside track-word names keep visitable premises.
    assert spider._is_dropped_name("Töölön kisahalli / Juoksusuora") is None
    assert spider._is_dropped_name("Juoksusuora, Kalajoen jäähalli") is None
    assert spider._is_dropped_name("Vantaan Reittipuiston lentopallokenttä") is None
    assert spider._is_dropped_name("Latupuiston päiväkoti") is None
    assert spider._is_dropped_name("Latukankadun leikkikenttä") is None
    assert spider._is_dropped_name("Pirkkolan liikuntapuisto (Kuntoradan alalenkki) / Ulkokuntoilupaikka") is None
    # Bare compounds, school tracks and park routes stay dropped.
    assert spider._is_dropped_name("Päiväkummun koulun juoksusuora ja pituushyppypaikka") == "non_place/track"
    assert spider._is_dropped_name("Keskuspuisto 1 latu 10,6 km") == "non_place/track"
    assert spider._is_dropped_name("Nevanlenkki") == "non_place/track"
    assert spider._is_dropped_name("Aulangon ulkoilumaja - golfkenttä -hiihtolatu (2 km)") == "non_place/track"
    assert spider._is_dropped_name("Sipoon Veden sähköpostiosoite") == "non_place/contact"
    assert spider._is_dropped_name("Seritatyön sähköpostiosoite") == "non_place/contact"
    assert spider.parse_channel(channel("Etsivä yksikkö")) is None
    assert spider.crawler.stats.get_value("ptv_fi/dropped/non_place/mobile") == 1


def test_located_value_hygiene():
    spider = make_spider()
    assert spider._clean_located_value("Kyläryhmä -palvelun järjestämispaikka, Virolahti 2", None) == "Kyläryhmä"
    assert spider._clean_located("Aurinkolahden peruskoulu (Solvindsgatan 11)") == "Aurinkolahden peruskoulu"
    assert spider._clean_located("Heteniitynkenttä (Vuosaari)") == "Heteniitynkenttä (Vuosaari)"
    assert spider._clean_located("Infopiste") is None
    assert spider._clean_located_value("Helsinki", "Helsinki") is None
    assert (
        PtvFISpider._lang_value([{"language": "fi", "value": ""}, {"language": "fi", "value": "Katu"}], "fi") == "Katu"
    )


def test_gazetteer_coverage_lists():
    # Gazetteer towns peel even mid-list; single-town names never enter;
    # venue tails still venue; paren coverage matches case-insensitively.
    spider = make_spider()
    full = "Ravitsemusterapia, Kustavi, Laitila, Masku, Mynämäki, Naantali, Nousiainen"
    assert spider._split_name(full, None) == ("Ravitsemusterapia", None, full)
    assert spider._split_paren("Palvelu, helsinki (Nousiainen, Laitila)", "Helsinki") == (
        "Palvelu",
        None,
        "Palvelu, helsinki (Nousiainen, Laitila)",
    )


def test_list_and_batch_counters():
    spider = make_spider()
    out = list(spider.parse(TextResponse(url="https://x/?page=1", body=b"nope", encoding="utf-8"), page=1))
    assert len(out) == 1 and "page=2" in out[0].url
    assert spider.crawler.stats.get_value("ptv_fi/page/bad_json") == 1
    out = list(spider.parse(TextResponse(url="https://x/?page=2", body=b"[]", encoding="utf-8"), page=2))
    assert len(out) == 1 and "page=3" in out[0].url
    assert spider.crawler.stats.get_value("ptv_fi/page/bad_shape") == 1
    assert list(spider.parse_batch(TextResponse(url="https://x/list", body=b"nope", encoding="utf-8"))) == []
    assert spider.crawler.stats.get_value("ptv_fi/batch/bad_json") == 1
    assert list(spider.parse_batch(TextResponse(url="https://x/list", body=b"{}", encoding="utf-8"))) == []
    assert spider.crawler.stats.get_value("ptv_fi/batch/bad_shape") == 1
    body = json.dumps({"itemList": [{"id": "a"}, {"noid": 1}, "x"], "pageCount": 1}).encode()
    out = list(spider.parse(TextResponse(url="https://x/?page=1", body=body, encoding="utf-8"), page=1))
    assert spider._ids == ["a"]
    assert spider.crawler.stats.get_value("ptv_fi/list/ids") == 1
    assert out and all(getattr(r, "errback", None) is not None for r in out)


def test_pagination_stops_on_repeated_ids():
    spider = make_spider()
    page = {"itemList": [{"id": "a"}]}
    out1 = list(
        spider.parse(TextResponse(url="https://x/list?page=1", body=json.dumps(page).encode(), encoding="utf-8"), 1)
    )
    assert any(isinstance(r, JsonRequest) and "page=2" in r.url for r in out1)
    out2 = list(
        spider.parse(TextResponse(url="https://x/list?page=2", body=json.dumps(page).encode(), encoding="utf-8"), 2)
    )
    assert not any("page=3" in getattr(r, "url", "") for r in out2)


def test_org_join_and_flush_paths():
    spider = make_spider()
    a = channel("A-linna", org="org-9")
    a["id"] = "aaaaaaaa-1111-4111-8111-111111111111"
    b = channel("B-talo", org="org-9")
    b["id"] = "bbbbbbbb-1111-4111-8111-111111111111"
    body = json.dumps([a, b]).encode()
    out = list(spider.parse_batch(TextResponse(url="https://x/list", body=body, encoding="utf-8")))
    assert len([r for r in out if isinstance(r, JsonRequest)]) == 1
    assert sorted(spider._pending) == ["org-9"]
    org_body = json.dumps(
        [{"id": "org-9", "organizationNames": [{"language": "fi", "value": "Testiyhdistys ry"}]}]
    ).encode()
    items = list(
        spider.parse_orgs(TextResponse(url="https://x/Organization/list?guids=org-9", body=org_body, encoding="utf-8"))
    )
    assert len(items) == 2
    assert all(i.get("operator") == "Testiyhdistys ry" for i in items)
    assert all(i["extras"].get("operator:type") == "private" for i in items)
    # Unreturned orgs flush operator-less on success like on failure.
    item = spider.parse_channel(channel("X", org="org-9"))
    spider._pending["org-9"] = [item]
    body = json.dumps([{"id": "org-1", "organizationNames": [{"language": "fi", "value": "A Oy"}]}]).encode()
    out = list(
        spider.parse_orgs(
            TextResponse(url="https://x/Organization/list?guids=org-1,org-9", body=body, encoding="utf-8")
        )
    )
    assert item in out
    assert item.get("operator") is None
    assert spider._pending == {}
    # Failed fetches still yield waiting items operator-less.
    item = Feature()
    item["ref"] = "r1"
    spider._pending["org-1"] = [item]
    failure = SimpleNamespace(request=SimpleNamespace(url="https://example.fi/api?guids=org-1"))
    out = list(spider.errback_orgs(failure))
    assert len(out) == 1
    assert "operator" not in out[0]
    assert spider.crawler.stats.get_value("ptv_fi/org/failed") == 1
    # Bad org payloads flush pending instead of trapping.
    item = Feature()
    item["name"] = "X"
    spider._pending["org-1"] = [item]

    assert list(spider.parse_orgs(TextResponse(url="https://x/?guids=org-1", body=b"nope", encoding="utf-8"))) == [item]
    assert spider._pending == {}


def test_unreturned_orgs_join_without_rerequest():
    # An org the API never returns (deleted/renamed row) must not trap
    # later batches: a re-request with the same URL dies in Scrapy's
    # dupefilter, stranding its items until close.
    spider = make_spider()
    a = channel("A-linna", org="org-9")
    a["id"] = "aaaaaaaa-1111-4111-8111-111111111111"
    out = list(spider.parse_batch(TextResponse(url="https://x/list", body=json.dumps([a]).encode(), encoding="utf-8")))
    reqs = [r for r in out if isinstance(r, JsonRequest)]
    assert len(reqs) == 1
    assert reqs[0].dont_filter is True
    # The API answers without org-9 (dispatched the way Scrapy does, with
    # the request's cb_kwargs as callback keywords): the item flushes
    # operator-less and org-9 is remembered as known-missing.
    req = reqs[0]
    items = list(req.callback(TextResponse(url=req.url, body=b"[]", encoding="utf-8"), **req.cb_kwargs))
    assert len(items) == 1
    assert items[0].get("operator") is None
    assert spider._org_names["org-9"] is None
    # A later batch for the same org joins at once: no new request, so
    # nothing for the dupefilter to swallow.
    b = channel("B-talo", org="org-9")
    b["id"] = "bbbbbbbb-1111-4111-8111-111111111111"
    out = list(spider.parse_batch(TextResponse(url="https://x/list", body=json.dumps([b]).encode(), encoding="utf-8")))
    assert not any(isinstance(r, JsonRequest) for r in out)
    assert len(out) == 1
    assert out[0].get("operator") is None
    assert spider._pending == {}


def test_crawl_errbacks_count_and_continue():
    spider = make_spider()
    failure = SimpleNamespace(request=SimpleNamespace(url="https://x/list?guids=a"))
    assert list(spider.errback_batch(failure)) == []
    assert spider.crawler.stats.get_value("ptv_fi/batch/failed") == 1
    spider._ids = ["a", "b"]
    first = list(spider.errback_list(failure))
    assert len(first) == 1
    assert spider.crawler.stats.get_value("ptv_fi/page/failed") == 1
    assert list(spider.errback_list(failure)) == []
    assert len(first) == 1


def test_crawl_hardening_record_guard_dedupe_and_resume():
    spider = make_spider()
    # One malformed record never kills its batch: the good row still joins.
    good = channel("A-linna", org="org-9")
    good["id"] = "aaaaaaaa-1111-4111-8111-111111111111"
    bad = channel("Bad record", org="org-9")
    bad["id"] = "bbbbbbbb-2222-4222-8222-222222222222"
    bad["services"] = ["x"]
    body = json.dumps([good, bad]).encode()
    out = list(spider.parse_batch(TextResponse(url="https://x/list", body=body, encoding="utf-8")))
    assert spider.crawler.stats.get_value("ptv_fi/batch/record_error") == 1
    assert sorted(spider._pending) == ["org-9"]
    assert any(isinstance(r, JsonRequest) for r in out)
    # Repeated list pages never duplicate detail fetches.
    spider = make_spider()
    page = {"itemList": [{"id": "a"}, {"id": "a"}], "pageCount": 1}
    list(spider.parse(SimpleNamespace(json=lambda: dict(page)), 1))
    assert spider._ids == ["a"]
    assert spider.crawler.stats.get_value("ptv_fi/list/ids") == 1
    # A dead mid-chain page skips ahead once, then falls through.
    spider = make_spider()
    spider._ids = ["a"]
    failure = SimpleNamespace(request=SimpleNamespace(url="https://x/?page=2", cb_kwargs={"page": 2}))
    out = list(spider.errback_list(failure))
    assert len(out) == 1 and "page=3" in out[0].url
    assert spider.crawler.stats.get_value("ptv_fi/page/skipped") == 1
    spider._page_skips = 3
    spider._seen_pages.add(4)
    resumed = list(
        spider.errback_list(SimpleNamespace(request=SimpleNamespace(url="https://x/?page=3", cb_kwargs={"page": 3})))
    )
    assert len(resumed) == 1  # falls through to the collected ids
    # Flushed orgs leave the seen set so later batches re-request them.
    spider = make_spider()
    item = Feature()
    item["ref"] = "r1"
    spider._pending["org-1"] = [item]
    spider._seen_orgs.add("org-1")
    failure = SimpleNamespace(request=SimpleNamespace(url="https://example.fi/api?guids=org-1"))
    assert list(spider.errback_orgs(failure)) == [item]
    assert "org-1" not in spider._seen_orgs


def test_special_exports_and_city_compounds():
    spider = make_spider()
    item = parsed(spider, channel("Punkalaitumen Nuorisotila"), "Punkalaitumen kunta")
    assert item["extras"]["amenity"] == "youth_centre"
    assert item.get("amenity") is None
    item = parsed(spider, channel("Töölöntori"), "Helsingin kaupunki")
    assert item["extras"]["place"] == "square"
    assert item.get("amenity") is None


def test_acronym_hosts_are_not_located():
    # Hospital-district acronyms operate the unit; they name no venue.
    item = parsed(make_spider(), channel("OYSin Keuhkosairauksien poliklinikka"))
    assert item.get("located_in") is None
    assert item["name"] == "Keuhkosairauksien poliklinikka"
    item = parsed(make_spider(), channel("Nuorisopsykiatrian osasto J1, Tyks"))
    assert item.get("located_in") is None
    assert item["name"] == "Nuorisopsykiatrian osasto J1"


def test_coordless_channels_are_kept():
    # Rows without usable coords stay as coordless items; the pipeline
    # strips bad geometry downstream instead of losing the service.
    data = channel("A-linna", org="org-9")
    data["id"] = "cccccccc-1111-4111-8111-111111111111"
    street = data["addresses"][0]["streetAddress"]
    street.pop("latitude", None)
    street.pop("longitude", None)
    item = parsed(make_spider(), data)
    assert item is not None
    assert item.get("lat") is None and item.get("lon") is None


def test_round22_flows():
    spider = make_spider()
    # Bare single-token street segments peel before room resolution.
    kentta = parsed(
        spider,
        channel("Iltapäivätoiminta / Pukinmäenkaaren peruskoulu / Kenttäkuja / Toiminta-alueittain"),
        "Helsingin kaupunki",
    )
    assert kentta.get("name") == "Iltapäivätoiminta"
    assert kentta.get("located_in") == "Pukinmäenkaaren peruskoulu"
    # Specialist dental units file dentist end to end.
    dent = parsed(spider, channel("Pirkanmaan suun erikoishoidon yksikkö - oikomishoito"), "Pirkanmaan hyvinvointialue")
    assert dent.get_tag("amenity") == "dentist"
    # Youth/pediatric wards file clinic and split hospital hosts.
    ward = parsed(
        spider, channel("Lasten ja nuorten päiväsairaala, Ahveniston sairaala"), "Kanta-Hämeen hyvinvointialue"
    )
    assert ward.get_tag("amenity") == "clinic"
    assert ward.get("name") == "Lasten ja nuorten päiväsairaala"
    assert ward.get("located_in") == "Ahveniston sairaala"


# ---- User-report batches ---------------------------------------------------------------
# One row per reported misparse, replay-verified. Static pins live here (not
# in the thematic tables) to keep a single home per feed string.


def test_user_report_facility_compounds():
    spider = make_spider()
    # 1. Fixed orienteering controls are markers, not the host park.
    assert cat(spider, "Keskuspuiston kiintorastit") == (None, None)
    item = parsed(spider, channel("Keskuspuiston kiintorastit"))
    assert item.get_tag("amenity") == "yes"
    assert item.get_tag("leisure") is None
    # 2. Tool-lending clean-up sheds (sv talkoskjul) are not piers.
    assert cat(spider, "Kaupunginpuutarhan talkoolaituri")[0] == Categories.TOOL_LIBRARY
    # 3. Sports parks file with sports centres; school hosts keep school filing.
    assert cat(spider, "Keski-Espoon urheilupuisto 2.")[0] == Categories.LEISURE_SPORTS_CENTRE
    assert cat(spider, "Urheilupuiston koulu")[0] == Categories.SCHOOL
    # 4. Borrowable city rowboats are boat rentals, not sports venues.
    assert cat(spider, "Kaupunkisoutuveneet")[0] == Categories.AMENITY_BOAT_RENTAL
    # 5. Park club activities are not the park.
    assert cat(spider, "Viherkallion asukaspuiston kerho") == (None, None)
    # 6. Allotment parcels on courthouse-named streets are allotments.
    assert cat(spider, "Käräjätuvan- ja Näsinojankuja, viljelypalstat")[0] == Categories.ALLOTMENTS


def test_user_report_batch_rb():
    spider = make_spider()
    # 1-2. Supervised-industry offices file as offices, not their topics.
    assert cat(spider, "Keski-Uudenmaan ympäristökeskus")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Kaupunkikehitys -toimiala")[0] == Categories.OFFICE_GOVERNMENT
    # 3. Power plants stay generic (wastewater-utility dumps).
    ch = channel("Vuosaaren voimalaitokset")
    ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": "jätevedenpuhdistamot"}]}]
    item = parsed(spider, ch)
    assert item.get_tag("amenity") == "yes"
    assert item.get_tag("leisure") is None
    # 4. Canoeing routes are routes, not rowing venues; genuine venues keep sports filing.
    assert cat(spider, "Melontareitti") == (None, None)
    ch = channel("Myyrmäen suuralueen kierros")
    ch["ontologyTerms"] = [{"name": [{"language": "fi", "value": "melontareitit"}]}]
    item = parsed(spider, ch)
    assert item.get_tag("amenity") == "yes"
    assert item.get_tag("leisure") is None
    assert cat(spider, "Melonta Kaartjärvellä")[0] == Categories.LEISURE_SPORTS_CENTRE
    assert cat(spider, "Kaukajärven soutu- ja melontastadion")[0] == Categories.LEISURE_SPORTS_CENTRE
    # 5. -aattori coinages are not squares; documented art files as art.
    assert cat(spider, "Väriaattori") == (None, None)
    ch = channel("Väriaattori", descriptions=[{"language": "en", "value": "Väriaattori is a work of public art"}])
    assert parsed(spider, ch).get_tag("tourism") == "artwork"


def test_user_report_batch_t():
    spider = make_spider()
    # Morgues have no enum entry: generic, never clinics or hospitals.
    assert cat(spider, "Vainajansäilytys, Ahveniston sairaala") == (None, None)
    assert cat(spider, "Helsingin vainajatilat") == (None, None)
    # Youth councils are civic offices, not youth venues; chambers keep events.
    assert cat(spider, "Nuorisovaltuusto")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Valtuustosali")[0] == Categories.EVENTS_VENUE
    # Nursing needs housing evidence; activities and labels fall through.
    assert cat(spider, "Ikäihmisten tehostettu palveluasuminen")[0] == Categories.NURSING_HOME
    assert cat(spider, "Ikäihmisten liikunta") == (None, None)
    assert cat(spider, "Ikäihmisten palvelujen hakemukset")[0] == Categories.OFFICE_GOVERNMENT


def test_user_report_batch_rc():
    spider = make_spider()
    # Pump-track tails name the POI like other facility tails.
    assert named(spider, "Malmin kenttä / Väliaikainen Pumptrack", "Helsinki") == (
        "Väliaikainen Pumptrack",
        "Malmin kenttä",
        "Malmin kenttä / Väliaikainen Pumptrack",
    )
    # Teaching-point branches of music schools: institution names the
    # POI, the site is the branch; school-hosted units keep located_in.
    item = parsed(spider, channel("Vantaan musiikkiopisto, Patotien pääopetuspiste"))
    assert item.get("name") == "Vantaan musiikkiopisto"
    assert item.get("branch") == "Patotien pääopetuspiste"
    assert item.get("located_in") is None
    assert named(spider, "Vantaan musiikkiopisto, Kartanonkosken koulun opetuspiste", "Vantaa") == (
        "Kartanonkosken koulun opetuspiste",
        "Vantaan musiikkiopisto",
        "Vantaan musiikkiopisto, Kartanonkosken koulun opetuspiste",
    )
    # Double-comma site qualifiers ride into located_in.
    assert named(spider, "Kouluravintola, Merilahden peruskoulu, Kallvikinniementien toimipiste", "Helsinki") == (
        "Kouluravintola",
        "Merilahden peruskoulu, Kallvikinniementien toimipiste",
        "Kouluravintola, Merilahden peruskoulu, Kallvikinniementien toimipiste",
    )
    # Senior gyms carry their clientele like senior social facilities.
    item = parsed(spider, channel("Hakunilan seniorikuntosali"))
    assert item.get_tag("leisure") == "fitness_centre"
    assert item["extras"].get("fitness_centre:for") == "senior"
    # Outdoor pools swim like indoor halls.
    assert cat(spider, "Keravan maauimala") == (Categories.LEISURE_SPORTS_CENTRE, {"sport": "swimming"})


def test_user_report_batch_rd():
    spider = make_spider()
    # Youth/adult mental-health and substance services are clinics, not
    # youth clubs: the nuoriso rule shadowed them.
    assert (
        cat(spider, "Perkkaan toimipiste, Nuorten ja Aikuisten mielenterveys- ja päihdepalvelut")[0]
        == Categories.CLINIC
    )
    assert (
        cat(spider, "Nummelan terveysasema, nuorten ja aikuisten mielenterveys- ja päihdepalvelut")[0]
        == Categories.CLINIC
    )
    assert cat(spider, "Nuorten sukupuoli-identiteetin tutkimusvastaanotto, Pasila")[0] == Categories.CLINIC
    # Housing still beats diagnosis without a youth stem; reception homes
    # house children round-the-clock, they are neither clinics nor clubs.
    assert (
        cat(spider, "Mielenterveys- ja päihdekuntoutujien asumispalveluyksiköt Tähkä ja Jyvä")[0]
        == Categories.SOCIAL_FACILITY
    )
    assert (
        cat(spider, "Konneveden, Uuraisten ja Äänekosken nuorten mielenterveys- ja päihdetyön tiimi")[0]
        == Categories.CLINIC
    )
    assert cat(spider, "Nuorten päihdepalvelu Pysäkki")[0] == Categories.CLINIC
    assert cat(spider, "Lasten ja nuorten mielenterveyspalvelut")[0] == Categories.CLINIC
    # Supervision units are government offices, not clinics or generics;
    # municipal vet branches keep their vet filing.
    assert cat(spider, "Terveysvalvonta")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Kalajoen kaupungin ympäristövalvonta")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Elintarviketurvallisuusyksikkö")[0] == Categories.OFFICE_GOVERNMENT
    assert cat(spider, "Ympäristöterveyspalvelut, Paraisten toimipiste")[0] == Categories.OFFICE_GOVERNMENT
    assert (
        cat(spider, "Ympäristönsuojelu- ja ympäristöterveyspalveluiden Iisalmen toimipiste")[0]
        == Categories.OFFICE_GOVERNMENT
    )
    assert (
        cat(spider, "Päijät-Hämeen ympäristöterveys, Orimattilan kunnaneläinlääkärin toimipiste")[0]
        == Categories.VETERINARY
    )
    # Slash-chain translations align per segment: the applied tail keeps
    # its rendering, located chains and truncated Finnish copies drop.
    item = parsed(
        spider,
        channel(
            "Iltapäivätoiminta / Vesalan peruskoulu / sivukoulu Ruuti, Helsingin Nuorten Miesten Kristillinen Y..",
            sv="Finskspråkig eftermiddagsverksamhet / Vesalan peruskoulu / sivukoulu Ruuti, Helsingin Nuorten Mies..",
            en="After-school activities / Vesala Comprehensive School / Ruuti, Helsinki YMCA",
        ),
    )
    assert item.get("name") == "Sivukoulu Ruuti, Helsingin Nuorten Miesten Kristillinen Y.."
    assert item["extras"].get("name:en") == "Ruuti, Helsinki YMCA"
    assert "name:sv" not in item["extras"]
