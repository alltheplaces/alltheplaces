from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class LoakeSpider(WPStoreLocatorSpider):
    name = "loake"
    item_attributes = {"brand": "Loake", "brand_wikidata": "Q22336859"}
    start_urls = ["https://www.loake.com/wp-admin/admin-ajax.php?action=store_search&filter=188&autoload=1"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["name"], item["branch"] = item["name"].split(" ", 1)

        apply_category(Categories.SHOP_SHOES, item)
        yield item
