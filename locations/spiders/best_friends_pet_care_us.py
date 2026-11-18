from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BestFriendsPetCareUSSpider(WPStoreLocatorSpider):
    name = "best_friends_pet_care_us"
    allowed_domains = ["bestfriendspetcare.com"]
    days = DAYS_EN
    start_urls = [
        "https://bestfriendspetcare.com/wp-admin/admin-ajax.php?action=store_search&lat=41.88325&lng=-87.6323879&max_results=500&search_radius=500"
    ]

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:

        if "best friends pet" in location.get("store").lower():
            item["brand"] = "Best Friends Pet Hotel"
            item["name"] = None
            item["branch"] = location.get("city")
        else:
            item["name"] = location.get("store")

        item["website"] = location.get("permalink")
        apply_category(Categories.ANIMAL_BOARDING, item)

        yield item
