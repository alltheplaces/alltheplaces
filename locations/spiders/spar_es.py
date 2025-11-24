from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.spar_aspiag import SPAR_SHARED_ATTRIBUTES
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider

BRANDS = {
    "SPAR EXPRESS": ({"name": "Spar Express"}, Categories.SHOP_CONVENIENCE),
    "SPAR": ({"name": "Spar"}, Categories.SHOP_CONVENIENCE),
    "EUROSPAR": ({"name": "Eurospar"}, Categories.SHOP_SUPERMARKET),
    "SPAR NATURAL": ({"name": "Spar Natural"}, Categories.SHOP_CONVENIENCE),
    "SPAR CITY": ({"name": "Spar City"}, Categories.SHOP_CONVENIENCE),
}


class SparESSpider(WPStoreLocatorSpider):
    name = "spar_es"
    item_attributes = SPAR_SHARED_ATTRIBUTES
    allowed_domains = ["spar.es"]

    def post_process_item(self, item: Feature, response: Response, shop: dict) -> Iterable[Feature]:
        store_type = "SPAR EXPRESS" if shop["store"].startswith("SPAR EXPRESS") else shop["store"]
        brand, category = BRANDS.get(store_type, ({}, None))
        item.update(brand)
        if category is not None:
            apply_category(category, item)

        yield item
