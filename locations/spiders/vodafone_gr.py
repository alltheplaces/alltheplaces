import re
from typing import Iterable

from scrapy.http import Response

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class VodafoneGRSpider(JSONBlobSpider):
    name = "vodafone_gr"
    item_attributes = {"brand": "Vodafone", "brand_wikidata": "Q122141"}
    start_urls = ["https://www.vodafone.gr/api/store"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    locations_key = ["data", "stores"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = feature.get("streetNameDefault")
        item["opening_hours"] = self.parse_opening_hours(feature)
        yield item

    def parse_opening_hours(self, feature: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in DAYS_FULL:
            hours = feature.get(f"{day.lower()}Hours") or ""
            for open_time, close_time in re.findall(r"(\d\d:\d\d)\s*-\s*(\d\d:\d\d)", hours):
                oh.add_range(day, open_time, close_time)
        return oh
