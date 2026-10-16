# -*- coding: utf-8 -*-
"""Behavioural tests for lipas_fi.

Each case pins a load-bearing rule: slash name splits (descriptor tails,
numbered facility-in-venue, institution hosts, multi-slash remainder),
chain brand anchors and their deliberate non-fires, plus ref/type-code
coercion. Cases use real LIPAS records (lipas-id in comments) unless marked
SYNTHETIC.
"""

import json
from types import SimpleNamespace

from scrapy.exceptions import CloseSpider
from scrapy.http import JsonRequest, TextResponse

from locations.items import Feature
from locations.spiders.government.lipas_fi import LipasFISpider


class _Stats:
    def __init__(self):
        self.d = {}

    def inc_value(self, key, n=1):
        self.d[key] = self.d.get(key, 0) + n

    def get_value(self, key, default=0):
        return self.d.get(key, default)


def make_spider():
    spider = LipasFISpider()
    spider.crawler = SimpleNamespace(stats=_Stats())
    return spider


def named(spider, raw_name, type_code):
    item = Feature()
    spider._apply_name(item, type_code, raw_name)
    spider._apply_brand(item, type_code)
    return item


def test_descriptor_tail_names_head():
    # 503356: tail restates the record's own type, head is the name.
    spider = make_spider()
    item = named(spider, "Leikkipuisto Orava / Luistelukenttä", 1520)
    assert item["name"] == "Leikkipuisto Orava"
    assert "located_in" not in item
    assert item["extras"]["official_name"] == "Leikkipuisto Orava / Luistelukenttä"
    assert spider.crawler.stats.get_value("atp/lipas_fi/name/split_slash") == 1


def test_numbered_tail_is_facility_in_venue():
    # 503455: numbered tail names the facility inside the venue.
    item = named(make_spider(), "Kallahdenkenttä / Luistelukenttä 1", 1520)
    assert item["name"] == "Luistelukenttä 1"
    assert item.get("located_in") == "Kallahdenkenttä"
    assert item["extras"]["official_name"] == "Kallahdenkenttä / Luistelukenttä 1"


def test_institution_head_hosts_facility():
    # SYNTHETIC: institution heads always host, never name the POI.
    item = named(make_spider(), "Munkkivuoren ala-asteen koulu / Liikuntasali", 2150)
    assert item["name"] == "Liikuntasali"
    assert item.get("located_in") == "Munkkivuoren ala-asteen koulu"
    assert item["extras"]["official_name"] == "Munkkivuoren ala-asteen koulu / Liikuntasali"


def test_compound_tail_matches_end_anchored():
    # SYNTHETIC: tail compound ends with the record's own type name.
    item = named(make_spider(), "Kenttä X / Jääkiekkokaukalo", 1530)
    assert item["name"] == "Kenttä X"
    assert item["extras"]["official_name"] == "Kenttä X / Jääkiekkokaukalo"


def test_type_alternative_tail_matches():
    # SYNTHETIC: "laavu" is one alternative of type 301 "laavu, kota tai kammi".
    item = named(make_spider(), "Metsä / Laavu", 301)
    assert item["name"] == "Metsä"
    assert item["extras"]["official_name"] == "Metsä / Laavu"


def test_multi_slash_keeps_remainder():
    # 77557: only the last " / " splits; the head remainder stays intact.
    item = named(make_spider(), "Paloheinä Golf / Iso Ysi / Jokamiesgolfkenttä", 1650)
    assert item["name"] == "Paloheinä Golf / Iso Ysi"
    assert item["extras"]["official_name"] == "Paloheinä Golf / Iso Ysi / Jokamiesgolfkenttä"


def test_non_matching_tail_stays_whole():
    # SYNTHETIC: tail is not the record's type, institution or number.
    item = named(make_spider(), "Väinämöisenkenttä / Luistelukenttä", 1340)
    assert item["name"] == "Väinämöisenkenttä / Luistelukenttä"
    assert "official_name" not in item["extras"]


def test_degenerate_slash_keeps_survivor_or_drops():
    spider = make_spider()
    item = Feature()
    spider._apply_name(item, 1520, "Kenttä / ")
    assert item["name"] == "Kenttä"
    # Build level strips stray leading/trailing slashes before naming.
    assert build(spider, "Kenttä / ", 1520)["name"] == "Kenttä"
    assert build(spider, " / ", 1520) is None


def test_brands_tag_and_keep_branch():
    # 507393, 608484, 521665.
    spider = make_spider()
    item = named(spider, "Kuntokeskus Liikku Hermia", 2110)
    assert item["name"] == "Kuntokeskus Liikku Hermia"
    assert item["brand"] == "Kuntokeskus Liikku"
    assert item["brand_wikidata"] == "Q28721474"
    item = named(spider, "Liikku Rantaperkiö", 2120)
    assert item["brand"] == "Kuntokeskus Liikku"
    assert item["brand_wikidata"] == "Q28721474"
    item = named(spider, "Fitness24Seven Kauppakulma", 2110)
    assert item["brand"] == "Fitness24Seven"
    assert item["brand_wikidata"] == "Q61112447"
    assert spider.crawler.stats.get_value("atp/lipas_fi/brand/kuntokeskus_liikku") == 1
    assert spider.crawler.stats.get_value("atp/lipas_fi/brand/liikku") == 1
    # 529401: spaced variant with first-party domain proof.
    item = named(spider, "Fitness 24/7 Olari", 2120)
    assert item["brand"] == "Fitness24Seven"
    assert item["brand_wikidata"] == "Q61112447"
    # 2026-10-15 Wikidata brand items Q141740469-Q141740472.
    for raw, brand, qid in (
        ("EasyFit Kerava", "EasyFit", "Q141740469"),
        ("LadyLine Loimaa", "LadyLine", "Q141740470"),
        ("Forever Varisto", "Forever", "Q141740471"),
        ("GoGo City", "GOGO Liikuntakeskus", "Q141740472"),
    ):
        item = named(spider, raw, 2110)
        assert item["brand"] == brand and item["brand_wikidata"] == qid, raw


def test_brands_do_not_fire_on_pending_or_excluded_names():
    # 77994, 77870: Fressi/Elixia have no brand item yet, so never branded.
    for raw in ("Fressi Kamppi / Kuntokeskus", "ELIXIA Pitäjänmäki / Kuntokeskus"):
        item = named(make_spider(), raw, 2110)
        assert not item.get("brand") and not item.get("brand_wikidata"), raw
    # GoGo Express Oy is a separate company: "gogo express" must not take the
    # GOGO anchor even though it prefix-matches it.
    for raw in ("GOGO Express Lielahti", "GoGo Express Seppälä"):
        item = named(make_spider(), raw, 2110)
        assert not item.get("brand") and not item.get("brand_wikidata"), raw
    # 522623: "liikku" mid-word is not the chain anchor.
    item = named(make_spider(), "Fysiokeskus Ikiliikkujan kuntosali", 2120)
    assert not item.get("brand")
    # SYNTHETIC: prefix without word boundary is not the anchor either.
    item = named(make_spider(), "Liikkuja Areena", 2120)
    assert not item.get("brand") and not item.get("brand_wikidata")
    # SYNTHETIC: non-gym types never brand.
    item = named(make_spider(), "Liikku Halli", 2150)
    assert not item.get("brand")


def build(spider, name="Kenttä", type_code=1520, **overrides):
    record = {
        "lipas-id": 1,
        "type": {"type-code": type_code},
        "name": name,
        "status": "active",
        "location": {
            "address": "Katu 1",
            "postal-code": "00100",
            "postal-office": "Helsinki",
            "geometries": {"features": [{"geometry": {"type": "Point", "coordinates": [24.9, 60.1]}}]},
        },
    }
    record.update(overrides)
    if "location" in overrides:
        record["location"] = overrides["location"]
    return spider._build_item(record)


def location(**overrides):
    base = {
        "address": "Katu 1",
        "postal-code": "00100",
        "postal-office": "Helsinki",
        "geometries": {"features": [{"geometry": {"type": "Point", "coordinates": [24.9, 60.1]}}]},
    }
    base.update(overrides)
    return base


def test_ref_normalises_whole_floats_and_unhashable_type_falls_back():
    spider = make_spider()

    def build_id(lipas_id, type_code):
        record = {
            "lipas-id": lipas_id,
            "type": {"type-code": type_code},
            "name": "Kenttä",
            "status": "active",
            "location": location(),
        }
        return spider._build_item(record)

    assert build_id(74702.0, 1520)["ref"] == "74702"  # SYNTHETIC float-typed id
    assert build_id(" 74702 ", 1520)["ref"] == "74702"
    fallback = build_id(1, ["1520"])  # SYNTHETIC unhashable code
    assert fallback is not None and fallback["ref"] == "1"
    assert fallback.get_tag("amenity") == "yes"
    assert fallback.get_tag("leisure") is None
    assert fallback.get_tag("sport") is None
    for bad_id in (None, True, float("nan"), "", "  ", [], {}):
        assert build_id(bad_id, 1520) is None


def test_excluded_unknown_and_closed_records():
    spider = make_spider()
    assert build(spider, type_code=4401) is None  # linear route excluded
    assert build(spider, type_code=7000) is None  # maintenance building excluded
    assert spider.crawler.stats.get_value("atp/lipas_fi/excluded/4401") == 1
    unknown = build(spider, type_code=99999)  # SYNTHETIC future code
    assert unknown is not None and unknown.get_tag("amenity") == "yes"
    assert spider.crawler.stats.get_value("atp/lipas_fi/unmapped/99999") == 1
    assert build(spider, status="closed") is None
    assert build(spider, status=" Active ") is not None
    assert build(spider, type_code="1520") is not None  # numeric-string code
    nogeom = location(geometries={"features": []})
    assert build(spider, location=nogeom) is not None  # address saves it
    assert build(spider, location={"address": "-", "geometries": {"features": []}}) is None


def test_text_guards_and_website_branches():
    assert LipasFISpider._text("Roihuvuoren ala-\u200basteen koulu") == "Roihuvuoren ala-asteen koulu"
    assert LipasFISpider._text("Myyrmäen  uimahallin   kuntosali") == "Myyrmäen uimahallin kuntosali"
    assert LipasFISpider._text(40100.0) == "40100"
    assert LipasFISpider._text(True) == ""
    assert LipasFISpider._is_placeholder("0.0") and LipasFISpider._is_placeholder("–")
    norm = make_spider()._normalize_website
    assert norm("https:/korsholm.fi/valfard") == "https://korsholm.fi/valfard"
    assert norm("example.fi") == "https://example.fi"
    assert norm("a b.fi") is None
    assert norm("https://") is None
    assert norm("HTTPS://") is None
    # Upstream scheme typos are repaired, not dropped.
    assert norm("hhttps://www.kankaanpaa.fi/x") == "https://www.kankaanpaa.fi/x"
    assert norm("ps://www.iisalmi.fi/x") == "https://www.iisalmi.fi/x"
    assert norm("hpps://palaute.kuopio.fi") == "https://palaute.kuopio.fi"
    assert norm("-https://koski.fi/x") == "https://koski.fi/x"
    assert norm(":www.stellamaria.fi") == "https://www.stellamaria.fi"
    # Comma-for-dot host typos are repaired.
    assert norm("www.tornio,fi") == "https://www.tornio.fi"
    assert norm("www,vihti.fi") == "https://www.vihti.fi"
    # Punycode and malformed hosts are dropped instead of ERRORing downstream.
    assert norm("https://www.xn--metsmaa-8wa.fi/x") is None
    assert norm("http://www.muurame./hiihtoladut") is None


def test_city_paren_stripped_and_collection_recurses():
    spider = make_spider()
    item = build(spider, location=location(**{"postal-office": "Otalampi (Vihti)"}))
    assert item["city"] == "Otalampi"
    item = build(
        spider,
        location=location(
            geometries={
                "features": [
                    {
                        "geometry": {
                            "type": "GeometryCollection",
                            "geometries": [{"type": "Point", "coordinates": [24.9, 60.1]}],
                        }
                    }
                ]
            }
        ),
    )
    assert (item["lon"], item["lat"]) == (24.9, 60.1)


def test_largest_ring_wins_and_inf_code_falls_back():
    spider = make_spider()
    site = {
        "location": {
            "geometries": {
                "features": [
                    {
                        "geometry": {
                            "type": "MultiPolygon",
                            "coordinates": [
                                [[[0.0, 0.0], [0.0, 10.0], [10.0, 10.0], [10.0, 0.0], [0.0, 0.0]]],
                                [[[100.0, 100.0], [100.0, 101.0], [101.0, 101.0], [101.0, 100.0], [100.0, 100.0]]],
                            ],
                        }
                    }
                ]
            }
        }
    }
    assert spider._point(site) == (5.0, 5.0)
    assert spider.crawler.stats.get_value("atp/lipas_fi/geometry/polygon_centroid") == 1
    assert build(spider, type_code=float("inf")) is not None
    assert build(spider, type_code={"code": 1520}) is not None


def test_fractional_codes_and_unknown_geometry():
    spider = make_spider()
    # SYNTHETIC: a fractional code must not truncate to 1520.
    frac = build(spider, type_code=1520.5)
    assert frac is not None and frac.get_tag("leisure") is None
    assert spider.crawler.stats.get_value("atp/lipas_fi/unmapped/None") == 1
    # Tuple-typed MultiPoint coordinates still resolve the first finite point.
    assert LipasFISpider._first_point(((None, None), (24.5, 60.2))) == (24.5, 60.2)
    # SYNTHETIC: an unknown geometry type is counted, not silently ignored.
    weird = {"location": {"geometries": {"features": [{"geometry": {"type": "Circle", "coordinates": [1, 2, 3]}}]}}}
    assert spider._point(weird) is None
    assert spider.crawler.stats.get_value("atp/lipas_fi/geometry/unknown_type") == 1


def first_page(spider, payload):
    response = TextResponse(
        url="https://api.lipas.fi/v2/sports-sites?page=1",
        body=json.dumps(payload).encode(),
        encoding="utf-8",
    )
    return list(spider.parse_first_page(response))


def test_first_page_flows_guards_and_pagination():
    spider = make_spider()
    item_payload = {
        "lipas-id": 1,
        "type": {"type-code": 1520},
        "name": "Kenttä",
        "status": "active",
        "location": location(),
    }
    # Valid first page: item first, then one request per remaining page.
    out = first_page(spider, {"items": [item_payload], "pagination": {"total-pages": 3}})
    assert out[0]["ref"] == "1" and not hasattr(out[0], "url")
    requests = [r for r in out[1:] if isinstance(r, JsonRequest)]
    assert [r.url for r in requests] == [
        "https://api.lipas.fi/v2/sports-sites?page=2&page-size=100&statuses=active,out-of-service-temporarily",
        "https://api.lipas.fi/v2/sports-sites?page=3&page-size=100&statuses=active,out-of-service-temporarily",
    ]
    # Corrupt envelopes fail fast instead of crawling empty.
    for bad in (
        {"items": [], "pagination": {"total-pages": 3}},
        {"items": {"a": 1}, "pagination": {"total-pages": 3}},
        {"items": [item_payload], "pagination": "x"},
        {"items": [item_payload], "pagination": [1]},
    ):
        try:
            first_page(make_spider(), bad)
        except CloseSpider:
            continue
        raise AssertionError(f"no CloseSpider for {bad!r}")


def test_page_error_retries_once_then_drops():
    spider = make_spider()

    def failure(url, retried):
        request = SimpleNamespace(url=url, meta={"retried": retried} if retried else {}, callback=None, errback=None)
        return SimpleNamespace(request=request)

    retry = list(spider.parse_page_error(failure("https://x/?page=7", False)))
    assert len(retry) == 1 and isinstance(retry[0], JsonRequest) and retry[0].meta.get("retried") is True
    assert list(spider.parse_page_error(failure("https://x/?page=7", True))) == []
    assert spider.crawler.stats.get_value("atp/lipas_fi/page/failed") == 1
    assert spider.crawler.stats.get_value("atp/lipas_fi/page/retried") == 1


def test_hostile_record_skipped_phone_passes_through():
    spider = make_spider()
    hostile = {
        "lipas-id": 1,
        "type": {"type-code": 1520},
        "name": ["Kenttä"],
        "status": "active",
        "phone-number": True,
        "email": {"a": 1},
        "www": "n/a",
        "location": {"address": {"k": "v"}, "geometries": {"features": []}},
    }
    assert spider._build_item(hostile) is None
    assert spider.crawler.stats.get_value("atp/lipas_fi/skipped/no_name") == 1
