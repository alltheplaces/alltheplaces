import json
from typing import Any, Iterable

from scrapy.http import TextResponse
from scrapy.spiders import Spider

from locations.categories import apply_category, Categories
from locations.dict_parser import DictParser


class CoffeebrandsSpider(Spider):
    name = "coffeebrands"
    item_attributes = {"brand": "Coffeebrands", "brand_wikidata": "Q122956019"}
    start_urls = ["https://coffeebrands.gr/stores"]
    wanted_types = ["CafeOrCoffeeShop"]

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[dict]:
        for location in json.loads(response.xpath('//*[contains(text(),"latitude")]/text()').get()).get(
            "itemListElement"
        ):
            location.update(location.pop("item"))
            item = DictParser.parse(location)
            item["ref"] = location.get("position")
            item["branch"] = item.pop("name").removeprefix("Coffeebrands, ")
            item["name"] = self.item_attributes["brand"]
            apply_category(Categories.COFFEE_SHOP, item)
            yield item
