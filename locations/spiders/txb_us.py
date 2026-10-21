from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class TxbUSSpider(WPStoreLocatorSpider):
    name = "txb_us"
    item_attributes = {"brand": "TXB"}
    # The endpoint answers "0" to the autoload request; one wide radius search returns every store.
    start_urls = [
        "https://txbstores.com/wp-admin/admin-ajax.php?action=store_search&lat=31.0&lng=-99.0&max_results=500&search_radius=2000&autoload=1"
    ]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None).removeprefix("TXB ")
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
