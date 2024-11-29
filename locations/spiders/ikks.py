import json
import re

import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_FR, OpeningHours


class IkksSpider(scrapy.Spider):
    name = "ikks"
    item_attributes = {"brand": "Ikks", "brand_wikidata": "Q3146711"}
    allowed_domains = ["stores.ikks.com"]
    start_urls = [
        "https://stores.ikks.com/mobify/proxy/ocapi/s/IKKS_COM/dw/shop/v21_3/stores?latitude=24.3356791&longitude=23.769953599999997&max_distance=20000&delivery_method=delivery&client_id=1c53da3a-3640-4a31-adad-0f43be6c0904&start=0&count=200"
    ]

    def parse(self, response):
        if not response.json().get("count"):
            return
        for data in response.json().get("data"):
            if "IKKS" in data.get("c_commercialSign"):
                item = DictParser.parse(data)
                oh = OpeningHours()
                for day in json.loads(data.get("c_workingSchedule")):
                    if not day.get("amBegin"):
                        continue
                    if day.get("amEnd") and day.get("pmBegin"):
                        oh.add_range(
                            day=DAYS_FR[day.get("title")[:2]], open_time=day.get("amBegin"), close_time=day.get("amEnd")
                        )
                        oh.add_range(
                            day=DAYS_FR[day.get("title")[:2]], open_time=day.get("pmBegin"), close_time=day.get("pmEnd")
                        )
                    else:
                        oh.add_range(
                            day=DAYS_FR[day.get("title")[:2]],
                            open_time=day.get("pmBegin") or day.get("amBegin"),
                            close_time=day.get("pmEnd"),
                        )
                item["opening_hours"] = oh.as_opening_hours()

                yield item

        start = int(re.findall("start=[0-9]+", response.url)[0][6:]) + 200
        url = f"https://stores.ikks.com/mobify/proxy/ocapi/s/IKKS_COM/dw/shop/v21_3/stores?latitude=24.3356791&longitude=23.769953599999997&max_distance=20000&delivery_method=delivery&client_id=1c53da3a-3640-4a31-adad-0f43be6c0904&start={start}&count=200"
        yield scrapy.Request(url=url, callback=self.parse)
