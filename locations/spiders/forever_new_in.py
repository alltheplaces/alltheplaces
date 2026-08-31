from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.forever_new_au_nz import FOREVER_NEW_SHARED_ATTRIBUTES
from locations.storefinders.stockinstore import StockInStoreSpider


class ForeverNewINSpider(StockInStoreSpider):
    name = "forever_new_in"
    item_attributes = FOREVER_NEW_SHARED_ATTRIBUTES
    api_site_id = "10396"
    api_widget_id = "400"
    api_widget_type = "storelocator"
    api_origin = "https://www.forevernew.co.in"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["ref"] = location["id"]
        item["website"] = None
        item["addr_full"] = item.pop("street_address")
        item["branch"] = item.pop("name").replace("Forever New - ", "")

        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
