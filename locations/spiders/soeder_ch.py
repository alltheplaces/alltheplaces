from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storemapper import StoremapperSpider


class SoederCHSpider(StoremapperSpider):
    name = "soeder_ch"
    item_attributes = {
        "brand_wikidata": "Q111722324",
        "brand": "Soeder",
    }
    company_id = "16023-r6PfOZv3OfbeGfgX"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        # Soeder has a few flagship stores under their own brand, but most stores
        # in their storefinder page are merely _selling_ Soeder products.
        if item.get("name") != "Soeder Store":
            return
        apply_category(Categories.SHOP_COSMETICS, item)
        yield item
