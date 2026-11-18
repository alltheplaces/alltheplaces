from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class GuessSpider(UberallSpider):
    name = "guess"
    item_attributes = {"brand": "Guess", "brand_wikidata": "Q2470307", "extras": Categories.SHOP_CLOTHES.value}
    key = "m8ENkkDpRuAzBfF8t5yWOETCTZ61PY"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        name = location["name"].casefold()
        if name == "guess accessories":
            apply_category(Categories.SHOP_FASHION_ACCESSORIES, item)
        elif name == "g by guess":
            item["brand_wikidata"] = "Q5515159"
        yield item
