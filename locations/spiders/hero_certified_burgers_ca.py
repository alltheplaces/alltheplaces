import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class HeroCertifiedBurgersCASpider(WPStoreLocatorSpider):
    name = "hero_certified_burgers_ca"
    item_attributes = {"brand": "Hero Certified Burgers", "brand_wikidata": "Q5742641"}
    start_urls = ["https://heroburgers.com/wp-admin/admin-ajax.php?action=store_search&autoload=1&lat=0&lng=0"]
    requires_proxy = True

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        branch = item.pop("name")
        if branch != "Hero Certified Burgers Virtual Kitchen":
            item["branch"] = re.sub(r"\s*\(Temporarily Closed\)$", "", branch)
        apply_category(Categories.FAST_FOOD, item)
        yield item
