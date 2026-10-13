from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class XtramartUSSpider(WPStoreLocatorSpider):
    name = "xtramart_us"
    item_attributes = {"brand": "XtraMart", "brand_wikidata": "Q119586946"}
    start_urls = ["https://xtramart.com/wp-admin/admin-ajax.php?action=store_search&autoload=1&lat=0&lng=0"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("XtraMart ")
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
