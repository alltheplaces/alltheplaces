from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class AldiSudITSpider(UberallSpider):
    name = "aldi_sud_it"
    item_attributes = {"brand_wikidata": "Q41171672"}
    key = "J8f9erNQcUhg1nmo5Bhp8wy2A6mQkK"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("ALDI ")
        item["phone"] = None
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
