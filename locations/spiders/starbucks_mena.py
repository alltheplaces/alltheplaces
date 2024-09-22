from typing import Any, Iterable

from scrapy import Request
from scrapy.http import JsonRequest, Response

from locations.categories import Extras, apply_yes_no
from locations.items import Feature, get_merged_item
from locations.storefinders.yext_search import YextSearchSpider

AMENITIES_MAP = {"Drive Through": Extras.DRIVE_THROUGH, "WiFi": Extras.WIFI}


class StarbucksMenaSpider(YextSearchSpider):
    name = name = "starbucks_mena"
    item_attributes = {"brand": "Starbucks", "brand_wikidata": "Q37158"}
    stored_items = {}

    def start_requests(self) -> Iterable[Request]:
        offset = 0
        yield JsonRequest(
            url=f"https://locations.starbucks.eg/index.html?search&r=250000&per={self.page_size}&offset={offset}"
        )
        yield JsonRequest(
            url=f"https://locations.starbucks.eg/ar?search&r=250000&per={self.page_size}&offset={offset}&l=ar"
        )

    def request_next_page(self, response: Response, **kwargs: Any) -> Any:
        pager = response.json()["queryParams"]
        offset = int(pager["offset"][0])
        page_size = int(pager["per"][0])
        if offset + page_size < response.json()["response"]["count"]:
            if "/ar?" in response.url:
                yield JsonRequest(
                    url=f"https://locations.starbucks.eg/ar?search&r=250000&per={self.page_size}&offset={offset + page_size}&l=ar"
                )
            else:
                yield JsonRequest(
                    url=f"https://locations.starbucks.eg/index.html?search&r=250000&per={self.page_size}&offset={offset + page_size}"
                )

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        if location["address"]["countryCode"] == "TR":  # Covered by starbucks_eu
            return
        if amenities := location.get("c_storeAmenities"):
            for amenity in amenities:
                if tag := AMENITIES_MAP.get(amenity):
                    apply_yes_no(tag, item, True)
                else:
                    self.crawler.stats.inc_value(f"atp/{self.name}/unknown_amenity/{amenity}")
        item["branch"] = location.get("c_siteLocation")
        if item["branch"] is None:
            item["branch"] = location.get("c_storeNameInternal")
        if item["ref"] in self.stored_items:
            other_item = self.stored_items.pop(item["ref"])
            if location["address"]["countryCode"] == "MA":
                other_language = "fr"
            else:
                other_language = "en"
            if location["meta"]["language"] == "ar":
                yield get_merged_item({other_language: other_item, "ar": item}, "ar")
            else:
                yield get_merged_item({other_language: item, "ar": other_item}, "ar")
        else:
            self.stored_items[item["ref"]] = item
