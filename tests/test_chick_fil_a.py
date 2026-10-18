import json

import pytest
from scrapy.http import TextResponse
from scrapy.utils.test import get_crawler

from locations.spiders.chick_fil_a import ChickFilASpider


def parse_profile(**properties):
    # Synthetic Yext response, not a downloaded store record. Playground values
    # follow the documented c_playground field on the spider's existing host:
    # https://locator.chick-fil-a.com.yext-cdn.com/search?q=
    profile = {
        "meta": {"uid": "test-store"},
        "name": "Chick-fil-A",
        "c_locationName": "Test Store",
        "c_status": "OPEN",
        "address": {"line1": "1 Test Street", "line2": None, "line3": None, "postalCode": "00000"},
        "c_carryout": True,
        "c_delivery": True,
        "c_hasDriveThru": True,
        "c_fullDineIn": True,
        **properties,
    }
    response = TextResponse(
        url="https://example.invalid/search",
        body=json.dumps(
            {
                "response": {"entities": [{"profile": profile}], "count": 1},
                "queryParams": {"offset": ["0"], "per": ["50"]},
            }
        ).encode(),
        encoding="utf-8",
    )
    spider = ChickFilASpider()
    spider.crawler = get_crawler(ChickFilASpider)
    return list(spider.parse(response))


@pytest.mark.parametrize("playground, kids_area, indoor", [("interior", "yes", "yes"), ("none", "no", None)])
def test_play_area(playground, kids_area, indoor):
    (item,) = parse_profile(c_playground=playground)
    assert item.get_tag("kids_area") == kids_area
    assert item.get_tag("kids_area:indoor") == indoor
    assert item.get_tag("kids_area:outdoor") is None
    assert item["ref"] == "test-store"
    assert item["branch"] == "Test Store"
    assert item.get_tag("takeaway") == "yes"
    assert item.get_tag("delivery") == "yes"
    assert item.get_tag("drive_through") == "yes"
    assert item.get_tag("indoor_seating") == "yes"


@pytest.mark.parametrize("properties", [{}, {"c_playground": None}, {"c_playground": ""}, {"c_playground": "unknown"}])
def test_missing_or_unknown_play_area(properties):
    (item,) = parse_profile(**properties)
    assert item.get_tag("kids_area") is None
    assert item.get_tag("kids_area:indoor") is None


def test_answers_services_does_not_override_playground():
    (item,) = parse_profile(c_playground="none", c_answersservices=["Playground"])
    assert item.get_tag("kids_area") == "no"
    assert item.get_tag("kids_area:indoor") is None


def test_future_store_is_still_skipped():
    assert parse_profile(c_status="FUTURE", c_playground="interior") == []
