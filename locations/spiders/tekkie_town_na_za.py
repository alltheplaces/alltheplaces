from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import apply_category, Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class TekkieTownNAZASpider(Spider):
    name = "tekkie_town_na_za"
    item_attributes = {"brand": "Tekkie Town", "brand_wikidata": "Q116620895"}
    start_urls = ["https://store-locator-shopify-app-d9f525452f2f.herokuapp.com/api/stores?brand=Tekkie%20Town"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("Tekkie Town").strip()
            item["ref"] = location["_id"]

            item["opening_hours"] = self.parse_opening_hours(location)
            apply_category(Categories.SHOP_SHOES, item)

            yield item

    def parse_opening_hours(self, location: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in map(str.lower, DAYS_FULL):
            rule = location["operating_hours"][day]
            oh.add_range(day, rule["open"], rule["close"], "%H:%M:%S")

        return oh
