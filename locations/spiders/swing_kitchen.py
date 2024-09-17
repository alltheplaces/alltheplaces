from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_DE
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SwingKitchenSpider(WPStoreLocatorSpider):
    name = "swing_kitchen"
    item_attributes = {"brand": "Swing Kitchen", "brand_wikidata": "Q116943226", "extras": Categories.FAST_FOOD.value}
    allowed_domains = [
        "www.swingkitchen.com",
    ]
    days = DAYS_DE

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("addr_full", None)
        item.pop("phone", None)
        yield item
