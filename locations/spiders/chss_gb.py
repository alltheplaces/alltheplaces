from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class ChssGBSpider(WPStoreLocatorSpider):
    name = "chss_gb"
    item_attributes = {
        "brand": "Chest, Heart and Stroke Scotland",
        "brand_wikidata": "Q30265706",
    }
    allowed_domains = ["www.chss.org.uk"]
    start_urls = [
        "https://www.chss.org.uk/wp-admin/admin-ajax.php?action=store_search&autoload=1&lat=55.9533&lng=-3.1883"
    ]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        apply_category(Categories.SHOP_CHARITY, item)
        yield item
