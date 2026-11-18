from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_NL
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class Optie1NLSpider(WPStoreLocatorSpider):
    name = "optie1_nl"
    item_attributes = {"brand": "Optie1", "brand_wikidata": "Q62393564"}
    start_urls = ["https://optie1.nl/wp-admin/admin-ajax.php?action=store_search&lat=52.1&lng=5.1&autoload=1"]
    days = DAYS_NL

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item
