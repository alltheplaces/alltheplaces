from typing import Iterable

from locations.items import Feature
from locations.storefinders.stockist import StockistSpider
from locations.categories import Categories, apply_category



class GoldUnionFRSpider(StockistSpider):
    name = "gold_union_fr"
    item_attributes = {"brand": "Gold Union", "brand_wikidata": "Q131622916"}
    key = "u20465"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_GOLD_BUYER, item)
        yield item
