from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class Devernois(StockistSpider):
    name = "devernois"
    item_attributes = {"brand": "Devernois", "brand_wikidata": "Q98778444"}
    key = "u15973"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("DEVERNOIS ")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
