from typing import Iterable
from urllib.parse import urljoin

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.forever_new_au_nz import FOREVER_NEW_SHARED_ATTRIBUTES
from locations.storefinders.stockinstore import StockInStoreSpider


class EverNewCASpider(StockInStoreSpider):
    name = "ever_new_ca"
    item_attributes = {**FOREVER_NEW_SHARED_ATTRIBUTES, "brand": "Ever New"}
    api_site_id = "10401"
    api_widget_id = "405"
    api_widget_type = "storelocator"
    api_origin = "https://www.evernew.ca"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("Ever New ", "")
        if page_url := location.get("store_locator_page_url"):
            item["website"] = urljoin(self.api_origin, page_url)
        else:
            item["website"] = None
        if item.get("email") == "evernew@evernew.ca":
            item["email"] = None

        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
