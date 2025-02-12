from typing import Any
from urllib.parse import urljoin

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class McdonaldsITSpider(scrapy.Spider):
    name = "mcdonalds_it"
    item_attributes = {"brand": "McDonald's", "brand_wikidata": "Q38076"}
    start_urls = ["https://www.mcdonalds.it/static/json/store_locator.json"]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["sites"]:
            store["street_address"] = store.pop("address")
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["website"] = urljoin("https://www.mcdonalds.it/ristorante/", store["uri"])

            for opening_hours in store["opening_hours"]:
                if opening_hours["name"] == "mccafe":
                    mccafe = item.deepcopy()
                    item["ref"] = "{}-mccafe".format(item["ref"])
                    mccafe["brand"] = "McCafé"
                    mccafe["brand_wikidata"] = "Q3114287"
                    apply_category(Categories.CAFE, mccafe)
                    mccafe["opening_hours"] = self.parse_opening_hours(opening_hours)
                    yield mccafe
                elif opening_hours["name"] == "mcdrive":
                    item["extras"]["opening_hours:drive_through"] = self.parse_opening_hours(opening_hours)
                elif opening_hours["name"] == "restaurant":
                    item["opening_hours"] = self.parse_opening_hours(opening_hours)

            apply_category(Categories.FAST_FOOD, item)

            yield item

    def parse_opening_hours(self, rules: dict) -> str:
        if rules["all24h"] is True:
            return "24/7"

        oh = OpeningHours()
        for rule in rules["days"]:
            oh.add_range(rule["name"], *rule["times"].split(","))

        return oh.as_opening_hours()
