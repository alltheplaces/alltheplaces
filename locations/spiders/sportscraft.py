from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class SportscraftSpider(StockistSpider):
    name = "sportscraft"
    item_attributes = {"brand": "Sportscraft", "brand_wikidata": "Q7579966"}
    key = "map_93wpxmnq"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
