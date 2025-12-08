from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class DrakesAUSpider(WPStoreLocatorSpider):
    name = "drakes_au"
    item_attributes = {"brand_wikidata": "Q48988077", "brand": "Drakes", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = [
        "drakes.com.au",
    ]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("addr_full", None)
        item.pop("email", None)
        item.pop("website", None)
        yield item
