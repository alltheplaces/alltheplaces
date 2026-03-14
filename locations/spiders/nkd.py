import json
from typing import Any

from scrapy.http import Response

from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class NkdSpider(JSONBlobSpider):
    name = "nkd"
    item_attributes = {"brand": "NKD", "brand_wikidata": "Q927272"}
    start_urls = ["https://www.nkd.com/media/storelocator.json"]

    def pre_process_data(self, location: dict) -> Any:
        location["street_address"] = location.pop("street")
        location["country"] = location.pop("country_id")
        if location["country"] == "US":
            # Locations in Croatia are labeled as "US" for some unknown reason
            location["country"] = "HR"
        location["ref"] = location.pop("source_code")
        location["website"] = "https://www.nkd.com/" + location.pop("url")

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Feature:
        item["branch"] = item.pop("name")
        item["name"] = "NKD"
        item["opening_hours"] = self.parse_opening_hours(location["frontend_description"])
        yield item

    @staticmethod
    def parse_opening_hours(hours_string: str) -> OpeningHours:
        hours = json.loads(hours_string)
        oh = OpeningHours()
        for day in map(str.lower, DAYS_3_LETTERS):
            if f"{day}_from" in hours and f"{day}_to" in hours:
                if hours.get(f"{day}_lunch_from", "") != "" and hours.get(f"{day}_lunch_to", "") != "":
                    oh.add_range(day, hours[f"{day}_from"], hours[f"{day}_lunch_from"])
                    oh.add_range(day, hours[f"{day}_lunch_to"], hours[f"{day}_to"])
                else:
                    oh.add_range(day, hours[f"{day}_from"], hours[f"{day}_to"])
        return oh
