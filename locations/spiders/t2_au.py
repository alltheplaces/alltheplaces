from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class T2AUSpider(StockistSpider):
    name = "t2_au"
    item_attributes = {"brand": "T2", "brand_wikidata": "Q48802134"}
    key = "map_4q6r4m5q"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("T2 - ")
        apply_category(Categories.SHOP_TEA, item)
        yield item
