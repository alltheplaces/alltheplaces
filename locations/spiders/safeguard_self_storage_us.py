from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import Request, TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature

ENDPOINTS_URL = "https://d162qya9roxth5.cloudfront.net/v4/endpoints/safeguard-self-storage"


class SafeguardSelfStorageUSSpider(Spider):
    name = "safeguard_self_storage_us"
    item_attributes = {"brand": "Safeguard Self Storage", "brand_wikidata": "Q127390353"}

    async def start(self) -> AsyncIterator[Request]:
        yield Request(f"{ENDPOINTS_URL}/v4_api_atlas_locations.json")

    def parse(self, response: TextResponse) -> Iterable[Request]:
        for location in response.json():
            yield Request(
                f"{ENDPOINTS_URL}/locations/{location['location_code']}/v4_api_atlas_location.json",
                callback=self.parse_location,
            )

    def parse_location(self, response: TextResponse) -> Iterable[Feature]:
        location = response.json()
        if location.get("status") != "published":
            return
        item = DictParser.parse(location)
        item["ref"] = location["fms_location_code"]
        item["branch"] = location["road_name"]
        item["street_address"] = item.pop("addr_full")
        item["state"] = location["contact_info"]["address"]["state"]
        item["website"] = "https://www.safeguardit.com/" + location["source_url"].split("/", 3)[3]

        item["opening_hours"] = OpeningHours()
        for office_hours in location.get("office_hours") or []:
            for line in office_hours["hours"].split("\n"):
                day, _, times = line.partition(":")
                if day in DAYS_FULL:
                    item["opening_hours"].add_ranges_from_string(f"{day} {times.strip()}")

        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
