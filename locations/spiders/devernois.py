from typing import Iterable

from locations.items import Feature
from locations.storefinders.stockist import StockistSpider
from locations.categories import Categories, apply_category



class Devernois(StockistSpider):
    name = "devernois"
    item_attributes = {"brand": "Devernois", "brand_wikidata": ""}
    key = "u15973"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("DEVERNOIS ")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
