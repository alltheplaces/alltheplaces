from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BarbarossaBaeckereiDESpider(WPStoreLocatorSpider):
    name = "barbarossa_baeckerei_de"
    item_attributes = {"brand_wikidata": "Q807766", "brand": "Barbarossa Bäckerei"}
    start_urls = [
        "https://www.barbarossa-baeckerei.de/wp-admin/admin-ajax.php?action=store_search&lat=49.440066&lng=7.749127&max_results=100&search_radius=100&distance_unit=km"
    ]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_BAKERY, item)
        yield item
