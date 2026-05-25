from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.carrefour_fr import parse_brand_and_category_from_mapping


class CarrefourTWSpider(Spider):
    name = "carrefour_tw"
    start_urls = ["https://www.uni-prosperity.com.tw/console/api/v1/stores?page_size=all"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    brands = {
        "量販": {
            "brand": "Carrefour",
            "brand_wikidata": "Q3117359",
            "category": Categories.SHOP_SUPERMARKET,
        },  # "Mass sales" (bad translation but as there are fewer of this type, it is probably the hypermarket brand)
        "超市": {"brand": "Carrefour Market", "brand_wikidata": "Q2689639", "category": Categories.SHOP_SUPERMARKET},
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["data"]["rows"]:
            if not location["status"]:
                continue
            item = DictParser.parse(location)
            if location["store_type_name"] not in self.brands.keys():
                continue
            parse_brand_and_category_from_mapping(item, location["store_type_name"], self.brands)
            item["phone"] = location["contact_tel"]
            item["website"] = item["extras"]["website:en"] = (
                "https://www.carrefour.com.tw/store-info-en/?store={}".format(location["name"])
            )
            item["extras"]["website:zh"] = "https://www.carrefour.com.tw/store-info/?store={}".format(location["name"])

            item["opening_hours"] = OpeningHours()
            if location["is24h"]:
                item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
            else:
                for day_name in ["mon", "tue", "wed", "thur", "fri", "sat", "sun"]:
                    if location.get(f"{day_name}_start") and location.get(f"{day_name}_end"):
                        item["opening_hours"].add_range(
                            day_name, location.get(f"{day_name}_start"), location.get(f"{day_name}_end")
                        )
            yield item
