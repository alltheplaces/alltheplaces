from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class CornishBakeryGBSpider(StockistSpider):
    name = "cornish_bakery_gb"
    item_attributes = {
        "brand_wikidata": "Q124030035",
        "brand": "Cornish Bakery",
    }
    key = "u10286"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_BAKERY, item)
        yield item
