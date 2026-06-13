from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BricksAndMinifigsSpider(WPStoreLocatorSpider):
    name = "bricks_and_minifigs"
    item_attributes = {"brand": "Bricks & Minifigs", "brand_wikidata": "Q109329121"}
    allowed_domains = ["bricksandminifigs.com"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if "coming soon" in item["street_address"].lower():
            return

        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_TOYS, item)
        yield item
