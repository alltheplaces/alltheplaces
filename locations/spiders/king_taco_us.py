from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class KingTacoUSSpider(WPStoreLocatorSpider):
    name = "king_taco_us"
    item_attributes = {"brand": "King Taco", "brand_wikidata": "Q6412104"}
    start_urls = [
        "https://kingtaco.com/wp-admin/admin-ajax.php?action=store_search&lat=34.054908&lng=-118.242643&autoload=1"
    ]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item.pop("name", None)
        apply_category(Categories.FAST_FOOD, item)
        yield item
