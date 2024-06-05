import json
import re

import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range


class FoodLionUSSpider(scrapy.Spider):
    name = "foodlion_us"
    item_attributes = {"brand": "Food Lion", "brand_wikidata": "Q1435950"}
    allowed_domains = ["www.foodlion.com"]
    start_urls = ["https://www.foodlion.com/stores/"]
    requires_proxy = True

    def start_requests(self):
        for state in ["GA", "SC", "NC", "MD", "TN", "VA"]:
            yield JsonRequest(url=f"https://www.foodlion.com/bin/foodlion/search/storelocator.json?state={state}")

    @staticmethod
    def parse_hours(hours: [str]) -> OpeningHours:
        oh = OpeningHours()
        for rule in hours:
            if rule == "Open 24 Hours":
                return "24/7"
            if m := re.match(
                r"(\w+)(?:-(\w+))?: (\d+:\d\d)\s*([ap]m)\s*-\s*(\d+:\d\d)\s*([ap]m)", rule.replace(".", "")
            ):
                start_day, end_day, start_time, start_zone, end_time, end_zone = m.groups()
                if not end_day:
                    end_day = start_day
                oh.add_days_range(
                    day_range(start_day, end_day),
                    f"{start_time} {start_zone}",
                    f"{end_time} {end_zone}",
                    time_format="%I:%M %p",
                )
        return oh

    def parse(self, response, **kwargs):
        for store in json.loads(response.json()["result"]):
            store["street_address"] = store.pop("address")
            item = DictParser.parse(store)
            item["website"] = f'https://www.foodlion.com{store["href"]}'

            item["opening_hours"] = self.parse_hours(store["hours"])

            yield item
