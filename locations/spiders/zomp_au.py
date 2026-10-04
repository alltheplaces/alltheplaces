from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.stockinstore import StockInStoreSpider


class ZompAUSpider(StockInStoreSpider):
    name = "zomp_au"
    item_attributes = {"brand": "ZOMP", "brand_wikidata": "Q117747772"}
    api_site_id = "10121"
    api_widget_id = "128"
    api_widget_type = "product"
    api_origin = "https://zomp.com.au"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_SHOES, item)
        yield item
