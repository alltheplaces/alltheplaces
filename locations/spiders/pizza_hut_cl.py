from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours


class PizzaHutCLSpider(Spider):
    name = "pizza_hut_cl"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    allowed_domains = ["api.mer-cat.com"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://api.mer-cat.com/v1/stores/all",
            headers={"PROJECT_ID": "WEB", "Accept": "application/json", "X-PLATFORM": "web", "X-TENANT": "pizzahut"},
        )

    def parse(self, response, **kwargs):
        for store in response.json():
            item = DictParser.parse(store)
            item["street_address"] = store.get("text_address")
            item["opening_hours"] = OpeningHours()
            for hours in store.get("business_hours"):
                day = hours["day"].capitalize()
                if day in DAYS_EN:
                    item["opening_hours"].add_range(
                        day,
                        hours["opening_time"].split(" ")[1],
                        hours["closing_time"].split(" ")[1],
                        time_format="%H:%M:%S",
                    )
            apply_category(Categories.RESTAURANT, item)
            yield item
