from typing import Iterable

from scrapy.http import TextResponse

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MilletsGBSpider(JSONBlobSpider):
    name = "millets_gb"
    item_attributes = {"brand": "Millets", "brand_wikidata": "Q64822903"}
    start_urls = [
        "https://integrations-c3f9339ff060a907cbd8.o2.myshopify.dev/api/stores?fid=ML00361,ML00758,ML01603,ML00339,ML00185,ML00478,ML00024,ML00249,ML00051,ML00023,ML00114,ML00372,ML00629,ML00889,ML00276,ML00375,ML00041,ML00175,ML00217,ML00995,ML00042,ML00327,ML00635,ML00286,ML00477,ML00675,ML00317,ML00396,ML01362,ML00379,ML00099,ML00125,ML00856,ML01945,ML00058,ML00180,ML00401,ML00318,ML00469,ML00718,ML00020"
    ]
    locations_key = "stores"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["street_address"] = feature["address_1"]
        item["phone"] = feature.get("local_phone")
        oh = OpeningHours()
        for day, time in feature["hours_sets"]["primary"]["days"].items():
            for open_close_time in time:
                open_time = open_close_time["open"]
                close_time = open_close_time["close"]
                oh.add_range(day, open_time, close_time)
        item["opening_hours"] = oh

        yield item
