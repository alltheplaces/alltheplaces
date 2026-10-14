from typing import Iterable

from scrapy.http import JsonRequest, TextResponse
from locations.categories import Categories, apply_category
from locations.storefinders.uberall import UberallSpider
from locations.items import Feature

class GuessSpider(UberallSpider):
    name = "guess"
    item_attributes = {"brand": "Guess", "brand_wikidata": "Q2470307", "extras": Categories.SHOP_CLOTHES.value}
    key = "m8ENkkDpRuAzBfF8t5yWOETCTZ61PY"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        print(location)
        if location["name"] == "Guess Accessories":
            apply_category(Categories.SHOP_FASHION_ACCESSORIES, feature)
        elif location["name"] == "G by Guess":
            item["brand_wikidata"] = "Q5515159"
        if location["name"] not in ("Clothing Store,GUESS", ""):
            item["brand"] = location["name"]
        yield item
