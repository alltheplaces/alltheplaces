from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BrewingzUSSpider(WPStoreLocatorSpider):
    name = "brewingz_us"
    item_attributes = {"brand": "BreWingZ", "brand_wikidata": "Q123022531"}
    start_urls = [
        "https://brewingz.com/wp-admin/admin-ajax.php?action=store_search&lat=29.7604267&lng=-95.3698028&max_results=100&search_radius=100"
    ]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["addr_full"] = item.pop("street_address")
        apply_category(Categories.RESTAURANT, item)
        yield item
