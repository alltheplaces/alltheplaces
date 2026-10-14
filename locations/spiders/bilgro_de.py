from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BilgroDESpider(WPStoreLocatorSpider):
    name = "bilgro_de"
    item_attributes = {"brand": "bilgro", "brand_wikidata": "Q108029888"}
    start_urls = ["https://www.bilgro.de/wp-admin/admin-ajax.php?action=store_search&autoload=1&lat=51&lng=10"]
    days = DAYS_DE

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item.pop("name", None)
        apply_category(Categories.SHOP_BEVERAGES, item)
        yield item
