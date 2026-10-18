import json

import pytest
from scrapy.http import TextResponse

from locations.spiders.mcdonalds import McdonaldsSpider


def parse_store(filter_type, **properties):
    # Synthetic locator fixture. Field names and flag values are documented in:
    # https://web.archive.org/web/20260108032830/https://www.mcdonalds.com/googleappsv2/geolocation?&latitude=28.520433&longitude=-81.58646&radius=80.45&maxResults=30&country=us&language=en-us&webStatusShowClosed=false&showClosed=&hours24Text=Open%2024%20hr
    store = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-84.0, 33.0]},
        "properties": {
            "identifierValue": "test-store",
            "name": "McDonald's Test Store",
            "filterType": filter_type,
            "indoorPlayGround": "0",
            "outDoorPlayGround": "0",
            **properties,
        },
    }
    response = TextResponse(
        url="https://example.invalid/locator",
        body=json.dumps({"features": [store]}).encode(),
        encoding="utf-8",
    )
    return list(McdonaldsSpider().parse_major_api(response, country="us", locale="en-us"))


@pytest.mark.parametrize(
    "filter_type, indoor",
    [
        (["PlayPlacePresence"], None),
        (["INDOORPLAYGROUND"], "yes"),
        (["PlayPlacePresence", "INDOORPLAYGROUND"], "yes"),
        (["restaurant.facility.INDOORPLAYGROUND"], "yes"),
        (["restaurant.facility.PlayPlacePresence"], None),
    ],
)
def test_play_area(filter_type, indoor):
    (item,) = parse_store(filter_type)
    assert item.get_tag("kids_area") == "yes"
    assert item.get_tag("kids_area:indoor") == indoor
    assert item.get_tag("kids_area:outdoor") is None
    assert item["ref"] == "test-store"
    assert item.get_tag("amenity") == "fast_food"


@pytest.mark.parametrize("filter_type", [[], ["WIFI"], ["UNKNOWNPLAYGROUND"]])
def test_missing_play_area_is_unknown(filter_type):
    (item,) = parse_store(filter_type)
    assert item.get_tag("kids_area") is None
    assert item.get_tag("kids_area:indoor") is None


def test_legacy_playground_fields_are_ignored():
    (item,) = parse_store([], indoorPlayGround="1", outDoorPlayGround="1")
    assert item.get_tag("kids_area") is None
    assert item.get_tag("kids_area:indoor") is None
    assert item.get_tag("kids_area:outdoor") is None


def test_other_amenities_are_preserved():
    (item,) = parse_store(["PlayPlacePresence", "DRIVETHRU", "WIFI", "MCDELIVERYSERVICE"])
    assert item.get_tag("kids_area") == "yes"
    assert item.get_tag("drive_through") == "yes"
    assert item.get_tag("internet_access") == "wlan"
    assert item.get_tag("delivery") == "yes"
