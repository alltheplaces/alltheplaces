from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class DmSpider(scrapy.Spider):
    name = "dm"
    item_attributes = {"brand": "dm", "brand_wikidata": "Q266572"}
    start_urls = [
        "https://store-data-service.services.dmtech.com/stores/bbox/55.2791403,5.4052295,48.5166335,17.5121631",
        "https://store-data-service.services.dmtech.com/stores/bbox/55.2791403,17.5121631,48.5166335,29.6190967",
        "https://store-data-service.services.dmtech.com/stores/bbox/48.5166335,5.4052295,40.7139891,17.5121631",
        "https://store-data-service.services.dmtech.com/stores/bbox/48.5166335,17.5121631,40.7139891,29.6190967",
    ]

    @staticmethod
    def parse_hours(store_hours: list[dict]) -> OpeningHours:
        opening_hours = OpeningHours()

        for store_day in store_hours:
            for times in store_day["timeRanges"]:
                opening_hours.add_range(DAYS[store_day["weekDay"] - 1], times["opening"], times["closing"])

        return opening_hours

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["stores"]:
            location["address"]["street_address"] = location["address"].pop("street")
            location["address"]["country"] = location["countryCode"]
            item = DictParser.parse(location)
            if location["countryCode"] in ["BG", "BA", "IT"]:
                item["website"] = (
                    f'https://www.dm-drogeriemarkt.{location["countryCode"].lower()}/store{location["storeUrlPath"]}'
                )
            elif location["countryCode"] == "SK":
                item["website"] = f'https://www.mojadm.sk/store{location["storeUrlPath"]}'
            else:
                item["website"] = f'https://www.dm.{location["countryCode"].lower()}/store{location["storeUrlPath"]}'
            item["extras"]["check_date"] = location["updateTimeStamp"].split("T", 1)[0]
            if location.get("openingHours"):
                item["opening_hours"] = self.parse_hours(location.get("openingHours"))

            apply_category(Categories.SHOP_CHEMIST, item)

            yield item
