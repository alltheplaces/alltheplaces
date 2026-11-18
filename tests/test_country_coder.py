import json

import pytest

from locations.country_coder import CountryCoder, canonical_id, resolve_location_set
from locations.name_suggestion_index import NSI_FILE_PATH


def feature(geometry: tuple[float, float] | None = None, **props) -> dict:
    """geometry is a (lon, lat) around which a small square polygon is built"""
    if geometry:
        lon, lat = geometry
        ring = [
            [lon - 0.1, lat - 0.1],
            [lon + 0.1, lat - 0.1],
            [lon + 0.1, lat + 0.1],
            [lon - 0.1, lat + 0.1],
            [lon - 0.1, lat - 0.1],
        ]
        geometry = {"type": "MultiPolygon", "coordinates": [[ring]]}
    return {"type": "Feature", "properties": props, "geometry": geometry}


# A hand-cut slice of country-coder's borders.json covering each shape the resolver has to handle.
BORDERS = {
    "type": "FeatureCollection",
    "features": [
        feature(m49="001", nameEn="World", level="world"),
        feature(m49="150", nameEn="Europe", level="region"),
        feature(m49="154", nameEn="Northern Europe", level="subregion", groups=["150"]),
        feature(m49="155", nameEn="Western Europe", level="subregion", groups=["150"]),
        feature(m49="002", nameEn="Africa", level="region"),
        feature(m49="015", nameEn="Northern Africa", level="subregion", groups=["002"]),
        feature(m49="003", nameEn="North America", level="subregion"),
        feature(m49="830", nameEn="Channel Islands", level="intermediateRegion", groups=["154", "150"]),
        feature(wikidata="Q35657", nameEn="US States", level="subcountryGroup", country="US"),
        feature(iso1A2="GB", iso1A3="GBR", iso1N3="826", nameEn="United Kingdom", aliases=["UK"]),
        feature((-1.5, 52.5), nameEn="England", country="GB", groups=["154", "150"], aliases=["GB-ENG"]),
        feature(iso1A2="GG", iso1N3="831", nameEn="Bailiwick of Guernsey", country="GB"),
        feature(nameEn="Guernsey", level="subterritory", country="GB", groups=["GG", "830", "154", "150"]),
        feature(
            iso1A2="CQ",
            iso1N3="680",
            nameEn="Sark",
            level="subterritory",
            country="GB",
            groups=["GG", "830", "154", "150"],
            isoStatus="excRes",
        ),
        feature(iso1A2="FR", iso1A3="FRA", iso1N3="250", nameEn="France"),
        feature(
            (2.3, 46.6),
            iso1A2="FX",
            iso1N3="249",
            nameEn="Metropolitan France",
            country="FR",
            groups=["155", "150"],
            isoStatus="excRes",
        ),
        feature((-61.5, 16.2), iso1A2="GP", iso1N3="312", nameEn="Guadeloupe", country="FR", groups=["029", "003"]),
        feature(iso1A2="ES", iso1A3="ESP", iso1N3="724", nameEn="Spain"),
        feature(nameEn="Peninsular Spain", country="ES", groups=["039", "150"]),
        feature((-5.3, 35.9), nameEn="Ceuta", level="subterritory", country="ES", groups=["EA", "015", "002"]),
        feature(iso1A2="EA", nameEn="Ceuta, Melilla", level="territory", country="ES", isoStatus="excRes"),
        feature(iso1A2="IC", nameEn="Canary Islands", country="ES", groups=["039", "150"], isoStatus="excRes"),
        feature(iso1A2="MA", iso1A3="MAR", iso1N3="504", nameEn="Morocco", groups=["015", "002"]),
        feature(iso1A2="US", iso1A3="USA", iso1N3="840", nameEn="United States of America"),
        feature(nameEn="Contiguous United States", country="US", groups=["Q35657", "021", "003"], aliases=["CONUS"]),
        feature(nameEn="Hawaii", country="US", groups=["Q35657", "061", "009"], aliases=["US-HI"]),
        feature(iso1A2="CA", iso1A3="CAN", iso1N3="124", nameEn="Canada", groups=["021", "003"]),
        feature(iso1A2="CY", iso1A3="CYP", iso1N3="196", nameEn="Cyprus", groups=["Q644636", "145"]),
        feature(wikidata="Q644636", nameEn="Cyprus", level="sharedLandform"),
        # de facto entity in country-coder: no ISO code, no country
        feature((33.3, 35.3), wikidata="Q23681", nameEn="Northern Cyprus", groups=["Q644636", "145", "142"]),
        feature(wikidata="Q37362", nameEn="Akrotiri and Dhekelia", aliases=["SBA"], country="GB"),
        feature(
            (32.98, 34.58),
            wikidata="Q9143535",
            nameEn="Akrotiri",
            level="subterritory",
            country="GB",
            groups=["Q644636", "Q37362", "145"],
        ),
        feature(iso1A2="CN", iso1A3="CHN", iso1N3="156", nameEn="China"),
        feature((114.2, 22.3), iso1A2="HK", iso1N3="344", nameEn="Hong Kong", country="CN"),
        feature(iso1A2="RU", iso1A3="RUS", iso1N3="643", nameEn="Russia"),
        feature(
            (34.0, 45.0), wikidata="Q7835", nameEn="Crimea", level="subterritory", country="RU", groups=["151", "150"]
        ),
        feature(iso1A2="UA", iso1A3="UKR", iso1N3="804", nameEn="Ukraine", groups=["151", "150"]),
        feature(iso1A2="XK", iso1A3="XKX", nameEn="Kosovo", groups=["039", "150"], isoStatus="usrAssn"),
        feature(iso1A2="EU", nameEn="European Union", level="union"),
    ],
}


@pytest.fixture(scope="module")
def coder() -> CountryCoder:
    return CountryCoder(BORDERS)


@pytest.mark.parametrize(
    "identifier, expected",
    [
        ("GB-ENG", "GBENG"),
        ("Northern Cyprus", "NORTHERNCYPRUS"),
        ("Ceuta, Melilla", "CEUTAMELILLA"),
        ("United States of America", "UNITEDSTATESAMERICA"),
        ("de", "DE"),
        (".de", ".DE"),
    ],
)
def test_canonical_id(identifier, expected):
    assert canonical_id(identifier) == expected


@pytest.mark.parametrize(
    "identifier, expected",
    [
        ("gb", {"gb"}),
        ("fr", {"fr", "gp"}),  # a country covers its ISO-coded territories, as in country-coder
        ("gp", {"gp"}),
        ("cn", {"cn"}),  # NSI keeps separate HK entries, so CN does not cover HK
        ("uk", {"gb"}),  # alias
        ("GBR", {"gb"}),  # ISO3
        ("826", {"gb"}),  # single-country M49
        ("fx", {"fr"}),  # exceptional reservation -> assigned code; Metropolitan France excludes Guadeloupe
        ("cq", {"gg"}),
        ("ea", {"es"}),
        ("xk", {"xk"}),  # user-assigned codes are kept
        (
            "150",
            {"gb", "gg", "fr", "es", "xk", "ua"},
        ),  # region: multi-part countries resolve to their country code; Crimea (subterritory) adds nothing
        ("830", {"gg"}),
        ("003", {"gp", "us", "ca"}),  # country-coder region unknown to the UN scheme
        ("015", {"ma"}),  # Ceuta (subterritory) does not put Spain in Africa
        ("conus", {"us"}),  # alias of a sub-country feature
        ("q35657", {"us"}),  # wikidata group
        ("northern cyprus", {"cy"}),  # no ISO code, no country in country-coder: what our geocoder says
        ("Q23681", {"cy"}),
        ("crimea", {"ua"}),  # country-coder says RU; our geocoder (hence our POIs) says UA
        ("sba", {"cy"}),  # group with no geometry: members geocoded as fallback
        ("Q644636", {"cy"}),  # landform: CY + Northern Cyprus + Akrotiri
        ("gb-eng", {"gb"}),
        ("001", None),  # world and unions are not indexed; callers special-case "001"
        ("eu", None),
        ("narnia", None),
    ],
)
def test_resolve(coder, identifier, expected):
    assert coder.resolve(identifier) == expected


def test_resolve_location_set(coder):
    location_set = {
        "include": ["fx", "us", "830", "gb-eng", "de-hamburg.geojson", "001", "conus", [-106, 34, 450]],
        "exclude": ["ic", "ea", [30, 30]],
    }
    assert resolve_location_set(location_set, coder) == {
        "include": ["001", "de-hamburg.geojson", "fr", "gb-eng", "gg", "mx", "us"],
        "exclude": ["es"],
    }


def test_resolve_location_set_keeps_unknown_and_logs(coder, caplog):
    assert resolve_location_set({"include": ["narnia"]}, coder, "brand-1") == {"include": ["narnia"]}
    assert "narnia" in caplog.text and "brand-1" in caplog.text


def test_resolve_location_set_preserves_empty_sides(coder):
    assert resolve_location_set({"include": ["001"], "exclude": []}, coder) == {"include": ["001"], "exclude": []}
    assert resolve_location_set({"include": ["ca"]}, coder) == {"include": ["ca"]}


def test_vendored_nsi_location_sets_are_resolved():
    """
    `scrapy vendor_nsi` must leave only what consumers match on. Fails when NSI starts using an identifier
    the resolver doesn't know — vendor_nsi logs it as an ERROR too.
    """
    nsi = json.load(open(NSI_FILE_PATH))["nsi"]
    unresolved = set()
    for tree in nsi.values():
        for item in tree["items"]:
            for side in ("include", "exclude"):
                for location in item["locationSet"].get(side, []):
                    if not isinstance(location, str):
                        unresolved.add(repr(location))
                    elif location == "001" or location.endswith(".geojson"):
                        continue
                    elif len(location) == 2 or (len(location) > 3 and location[2] == "-"):
                        continue
                    else:
                        unresolved.add(location)
    assert not unresolved, f"unresolved locationSet identifiers in nsi.json: {sorted(unresolved)[:20]}"
