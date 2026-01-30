from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class CheckersAndRallysUSSpider(scrapy.Spider):
    name = "checkers_and_rallys_us"
    brands = {
        "Checkers": {"brand": "Checkers", "brand_wikidata": "Q63919315"},
        "Rally's": {"brand": "Rally's", "brand_wikidata": "Q63919323"},
    }
    start_urls = ["https://checkersandrallys.com/unified-gateway/online-ordering/v1/all-stores/8159"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["stores_v1"]:
            location["address"].pop("id")
            location["address"].pop("name")
            location.update(location.pop("address"))
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").replace("Checkers ", "").replace("Rally's ", "")
            item["street_address"] = item.pop("street")
            item["addr_full"] = location["formatted_address"]
            if "Checkers" in location["name"]:
                item["brand"] = self.brands["Checkers"]["brand"]
                item["brand_wikidata"] = self.brands["Checkers"]["brand_wikidata"]
            elif "Rally's" in location["name"]:
                item["brand"] = self.brands["Rally's"]["brand"]
                item["brand_wikidata"] = self.brands["Rally's"]["brand_wikidata"]
            apply_category(Categories.FAST_FOOD, item)
            yield item
