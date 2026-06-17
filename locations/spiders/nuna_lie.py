from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class NunaLieSpider(StockistSpider):
    name = "nuna_lie"
    item_attributes = {"brand": "Nuna Lie", "brand_wikidata": "Q113291269"}
    key = "u11641"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
