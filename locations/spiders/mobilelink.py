from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class MobilelinkSpider(Spider):
    name = "mobilelink"
    item_attributes = {"brand": "Mobilelink"}
    allowed_domains = ["mobilelinkusa.com"]

    def start_requests(self):
        yield Request(
            url="https://mobilelinkusa.com/GetStores",
            method="POST",
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = location["Store"]
            item["phone"] = location["Contact"]

            oh = OpeningHours()
            for day in DAYS:
                if day == "Sa":
                    oh.add_range(day, location["SatOpentime"], location["SatClosetime"], "%H:%M:%S")
                elif day == "Su":
                    oh.add_range(day, location["SunOpentime"], location["SunClosetime"], "%H:%M:%S")
                else:
                    oh.add_range(day, location["Opentime"], location["Closetime"], "%H:%M:%S")
            item["opening_hours"] = oh

            yield item
