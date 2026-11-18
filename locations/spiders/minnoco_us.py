from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MinnocoUSSpider(WPStoreLocatorSpider):
    name = "minnoco_us"
    item_attributes = {"brand": "Minnoco"}
    # WP Store Locator returns nothing without lat/lng, even for autoload
    start_urls = ["https://www.minnoco.com/wp-admin/admin-ajax.php?action=store_search&autoload=1&lat=0&lng=0"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.FUEL_STATION, item)
        yield item
