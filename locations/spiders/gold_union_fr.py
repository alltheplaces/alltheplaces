from typing import Iterable

from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class GoldUnionFR(StockistSpider):
    name = "gold_union_fr"
    item_attributes = {"brand": "Gold Union", "brand_wikidata": ""}
    key = "u20465"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        yield item
