from typing import Iterable

from scrapy.http import TextResponse

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MilletsGBSpider(JSONBlobSpider):
    name = "millets_gb"
    item_attributes = {"brand": "Millets", "brand_wikidata": "Q64822903"}
    start_urls = [
        "https://integrations-c3f9339ff060a907cbd8.o2.myshopify.dev/api/stores?fascia=Millets&limit=48&radius=100"
    ]
    locations_key = "stores"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def pre_process_data(self, feature: dict) -> None:
        feature["ref"] = feature["address"]["postalCode"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            item["opening_hours"].add_range(
                day,
                feature["hours"][f"{day.lower()}"]["openIntervals"][0]["start"],
                feature["hours"][f"{day.lower()}"]["openIntervals"][0]["end"],
            )
        yield item
