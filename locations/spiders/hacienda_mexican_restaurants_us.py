from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class HaciendaMexicanRestaurantsUSSpider(WPStoreLocatorSpider):
    name = "hacienda_mexican_restaurants_us"
    item_attributes = {"brand": "Hacienda Mexican Restaurants"}
    # The endpoint answers "0" to the autoload request; one wide radius search returns every store.
    start_urls = [
        "https://www.haciendafiesta.com/wp-admin/admin-ajax.php?action=store_search&lat=41.6&lng=-86.2&max_results=100&search_radius=1000&autoload=1"
    ]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        # The head office is listed with the restaurants.
        if "Support Center" in feature.get("store", ""):
            return
        item["branch"] = item.pop("name", None)
        # Every entry carries the same office hours, not the restaurant's.
        item["opening_hours"] = None
        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "mexican"
        yield item
