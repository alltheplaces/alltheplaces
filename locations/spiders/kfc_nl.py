import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES


class KfcNLSpider(scrapy.Spider):
    name = "kfc_nl"
    start_urls = ["https://api.menu.app/api/directory/search"]
    item_attributes = KFC_SHARED_ATTRIBUTES

    def start_requests(self):
        yield JsonRequest(
            url="https://api.menu.app/api/directory/search",
            headers={"Application": "6a800bd9ae7e75ead64fc04c02a3f21a"},
            data={
                "latitude": "52.0907",
                "longitude": "5.1214",
                "order_types": [4, 6],
                "view": "search",
                "per_page": 500,
            },
            callback=self.parse,
        )

    def parse(self, response):
        for poi in response.json()["data"]["venues"]["data"]:
            poi = poi["venue"]
            item = DictParser.parse(poi)
            item.pop("state")
            item["street_address"] = item.pop("addr_full")
            self.parse_hours(item, poi)
            apply_category(Categories.FAST_FOOD, item)
            yield item

    def parse_hours(self, item, poi):
        days_map = {1: "Mo", 2: "Tu", 3: "We", 4: "Th", 5: "Fr", 6: "Sa", 0: "Su"}
        hours = poi.get("serving_times")
        if not hours:
            return
        oh = OpeningHours()
        for serving_time in hours:
            for day in serving_time.get("days", []):
                oh.add_range(days_map.get(day), serving_time.get("time_from"), serving_time.get("time_to"))
        item["opening_hours"] = oh.as_opening_hours()
