from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BricksMinifigsCAUSSpider(WPStoreLocatorSpider):
    name = "bricks_minifigs_ca_us"
    item_attributes = {
        "brand_wikidata": "Q109329121",
        "brand": "Bricks & Minifigs",
    }
    allowed_domains = [
        "bricksandminifigs.com",
    ]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_TOYS, item)
        yield item
