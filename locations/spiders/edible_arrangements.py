import json
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range


class EdibleArrangementsSpider(Spider):
    name = "edible_arrangements"
    item_attributes = {"brand": "Edible Arrangements", "brand_wikidata": "Q5337996"}
    allowed_domains = ["www.ediblearrangements.com"]

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            "https://www.ediblearrangements.com/stores/store-locator.aspx/GetStoresByCurrentLocation",
            method="POST",
            headers={
                "accept": "application/json, text/javascript, */*; q=0.01",
                "accept-language": "en-US,en;q=0.9",
                "content-type": "application/json; charset=UTF-8",
                "origin": "https://www.ediblearrangements.com",
                "referer": "https://www.ediblearrangements.com/stores/store-locator.aspx",
                "x-requested-with": "XMLHttpRequest",
            },
            body="{'Latitude' : '37.09024' , 'Longitude': '-95.712891','Distance':'5000'}",
            callback=self.parse,
        )

    def parse(self, response):
        d = json.loads(response.json()["d"])
        for shop in d["_Data"]:
            item = DictParser.parse(shop)
            oh = OpeningHours()
            for day_time in shop["TimingsShort"]:
                day = day_time["Days"]
                time = day_time["Timing"]
                if time == "Closed":
                    oh.set_closed(day)
                else:
                    start_day, end_day = day.split("-") if "-" in day else (day, day)
                    open_time, close_time = time.split("-")
                    oh.add_days_range(
                        day_range(start_day, end_day),
                        open_time=open_time.strip(),
                        close_time=close_time.strip(),
                        time_format="%I:%M %p",
                    )
                item["opening_hours"] = oh
            yield item
