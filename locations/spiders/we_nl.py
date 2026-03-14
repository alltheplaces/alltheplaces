import re

import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_NL, OpeningHours, sanitise_day


class WeNLSpider(scrapy.Spider):
    name = "we_nl"
    item_attributes = {"brand": "WE", "brand_wikidata": "Q1987861"}
    start_urls = [
        "https://www.wefashion.nl/s/WE-NL/dw/shop/v20_9/stores?client_id=f2fbfde0-02ea-4ad8-8864-5b6e62ad8c65&country_code=NL&longitude=52.1326&latitude=5.2913&count=200"
    ]

    def parse(self, response):
        for store in response.json().get("data"):
            opening_hours = OpeningHours()
            oh = store["store_hours"]
            days_hours = re.findall(
                r'<div class="floatLeft">(\w+)</div><div class="floatRight">(\d+:\d+)-(\d+:\d+)</div>', oh
            )
            for day_hour in days_hours:
                day = sanitise_day(day_hour[0], DAYS_NL)
                opening_hours.add_range(day=day, open_time=day_hour[1], close_time=day_hour[2])
            item = DictParser.parse(store)
            item["opening_hours"] = opening_hours
            yield item
