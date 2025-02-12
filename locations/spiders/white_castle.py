import re

import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class WhiteCastleSpider(scrapy.Spider):
    name = "white_castle"
    item_attributes = {"brand": "White Castle", "brand_wikidata": "Q1244034"}
    start_urls = ["https://www.whitecastle.com/api/vtl/get-nearest-location?lat=0&long=0distance=25000&count=1000"]

    custom_settings = {"ROBOTSTXT_OBEY": False}

    def store_hours(self, store):
        o = OpeningHours()

        for day_name in DAYS_FULL:
            key = day_name.lower() + "Hours"
            if key not in store:
                continue

            if store[key] == "24 hr":
                o.add_range(day_name[:2], "00:00", "23:59")
                continue

            open_time, close_time = store[key].split(" - ", 2)

            if close_time in ("12:00 AM", "12AM", "Midnight"):
                close_time = "11:59 PM"

            if bare_hour := re.match("([0-9]+)([AP]M)", open_time):
                open_time = f"{bare_hour[1]}:00 {bare_hour[2]}"
            if bare_hour := re.match("([0-9]+)([AP]M)", close_time):
                close_time = f"{bare_hour[1]}:00 {bare_hour[2]}"

            o.add_range(day_name[:2], open_time, close_time, time_format="%I:%M %p")

        return o

    def parse(self, response):
        for store in response.json()["results"]:
            # address is just the street address; here we correct it so DictParser chooses the right key
            store["street_address"] = store["address"]
            del store["address"]

            item = DictParser.parse(store)
            item["ref"] = store["storeNumber"]
            item["website"] = f'https://www.whitecastle.com/locations/{store.get("storeNumber")}'
            item["opening_hours"] = self.store_hours(store)

            yield item
