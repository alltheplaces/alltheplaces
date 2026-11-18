from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.stockinstore import StockInStoreSpider


class WranglerAUSpider(StockInStoreSpider):
    name = "wrangler_au"
    item_attributes = {"brand": "Wrangler", "brand_wikidata": "Q1445358"}
    api_site_id = "10061"
    api_widget_id = "68"
    api_widget_type = "sis"
    api_origin = "https://wrangler.com.au"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
