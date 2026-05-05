from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class BirdBlendGBSpider(StockistSpider):
    name = "bird_blend_gb"
    item_attributes = {"brand": "Bird & Blend Tea Co", "brand_wikidata": "Q116985265"}
    key = "map_9q94xv43"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_TEA, item)
        yield item
