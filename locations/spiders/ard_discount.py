from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_IT, OpeningHours, sanitise_day


class ArdDiscountSpider(Spider):
    name = "ard_discount"
    item_attributes = {"brand": "Ard Discount", "brand_wikidata": "Q105102666"}
    start_urls = ["https://portal.interattivo.net/api/app/get-markets?id_client=29&id_signboard=46"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["name"] = None
            item["city"] = item["city"]["name"]
            item["street_address"] = item.pop("addr_full")

            item["opening_hours"] = OpeningHours()
            for rule in location["openings"]:
                for times in rule["time"].split(" / "):
                    item["opening_hours"].add_range(sanitise_day(rule["day"], DAYS_IT), *times.split(" - "))
            yield item
