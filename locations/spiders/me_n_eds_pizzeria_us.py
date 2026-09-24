from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MeNEdsPizzeriaUSSpider(WPStoreLocatorSpider):
    name = "me_n_eds_pizzeria_us"
    item_attributes = {"brand": "Me-n-Ed's"}
    allowed_domains = ["www.meneds.com"]
    start_urls = [
        "https://www.meneds.com/wp-admin/admin-ajax.php?action=store_search&lat=36.7378&lng=-119.7871&max_results=200&search_radius=5000&autoload=1"
    ]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = "https://www.meneds.com/locations/"
        apply_category(Categories.FAST_FOOD, item)
        yield item
