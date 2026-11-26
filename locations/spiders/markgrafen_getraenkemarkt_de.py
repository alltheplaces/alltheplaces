from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MarkgrafenGetraenkemarktDESpider(WPStoreLocatorSpider):
    name = "markgrafen_getraenkemarkt_de"
    item_attributes = {"brand": "Markgrafen Getränkemarkt", "brand_wikidata": "Q100324493"}
    start_urls = [
        "https://www.markgrafen.com/wp-admin/admin-ajax.php?action=store_search&autoload=1&lat=52.0508132&lng=5.2854055"
    ]
    days = DAYS_DE

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["email"] = None
        item["website"] = "https://www.markgrafen.com/portfolio-items{}".format(item["website"])
        item["branch"] = item.pop("name")
        if item["phone"]:
            item["phone"] = item["phone"].replace("/", "")
        apply_category(Categories.SHOP_BEVERAGES, item)
        yield item
