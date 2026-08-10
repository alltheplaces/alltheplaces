import json

import scrapy
from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class BottlemartAUSpider(Spider):
    name = "bottlemart_au"
    item_attributes = {"brand": "Bottlemart", "brand_wikidata": "Q102863175"}
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    async def start(self):
        for city in city_locations("GB", 30000):
            yield scrapy.Request(
                url=f"https://bottlemart.com.au/api/geolocation/suburbs/search/{city['name']}",
                headers={
                    "tenant": "BM",
                },
            )

    def parse(self, response, **kwargs):
        if response.xpath("//pre/text()").get():
            for city in json.loads(response.xpath("//pre/text()").get()):
                yield JsonRequest(
                    url=f"https://bottlemart.com.au/api/members/search/{city['locality']}/{city['postal_code']}/{city['lat']}/{city['lon']}?maxDistance=200",
                    headers={
                        "tenant": "BM",
                    },
                    callback=self.parse_details,
                )

    def parse_details(self, response):
        for location in json.loads(response.xpath("//pre/text()").get()):
            item = DictParser.parse(location)
            item["ref"] = location["store_number"]
            item["state"] = location["address"].get("administrative_area")
            item["street_address"] = merge_address_lines(location["address"].get("lines"))
            try:
                oh = OpeningHours()
                for day, time in location["regular_hours"].items():
                    open_time = time.get("from")
                    close_time = time.get("until")
                    oh.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%I:%M %p")
                item["opening_hours"] = oh
            except:
                pass
            yield item
