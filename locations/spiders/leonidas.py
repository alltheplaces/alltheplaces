import json
from typing import Any

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class LeonidasSpider(scrapy.Spider):
    name = "leonidas"
    item_attributes = {"brand": "Leonidas", "brand_wikidata": "Q80335"}
    start_urls = ["https://www.leonidas.com/en/shops/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for data in json.loads(response.xpath("//@data-shops").get()):
            item = DictParser.parse(data)
            item["street_address"] = item.pop("street")
            if item.get("email"):
                item["email"] = item["email"][0]
            try:
                oh = OpeningHours()
                for key, value in data.get("schedule").items():
                    if value:
                        for time in value:
                            open_time = time[0]
                            close_time = time[1]
                            oh.add_range(day=key, open_time=open_time, close_time=close_time, time_format="%H:%M:%S")
                item["opening_hours"] = oh
            except:
                pass
            yield item
