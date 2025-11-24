from typing import Iterable

import scrapy
from scrapy import Request
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class ShopkoSpider(scrapy.Spider):
    name = "shopko"
    item_attributes = {"brand": "Shopko Optical", "brand_wikidata": "Q109228833"}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://api.scheduler.fielmannusa.com/api/FindNearestRetailStores",
            data={"latitude": 41.8780025, "longitude": -93.097702},
            method="POST",
        )

    def parse(self, response):
        for store in response.json():
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            oh = OpeningHours()
            for day, time in store["openingHours"].items():
                day = DAYS_FULL[int(day)]
                open_time, close_time = time.split(" - ")
                oh.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%H:%M %p")
            item["opening_hours"] = oh
            yield item
