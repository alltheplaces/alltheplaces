from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class VictraUSSpider(WPStoreLocatorSpider):
    name = "victra_us"
    item_attributes = {
        "brand": "Verizon",
        "brand_wikidata": "Q919641",
        "operator": "Victra",
        "operator_wikidata": "Q118402656",
        "extras": Categories.SHOP_MOBILE_PHONE.value,
    }
    allowed_domains = ["victra.com"]
    iseadgg_countries_list = ["US"]
    search_radius = 24
    max_results = 50
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if branch_name := item.pop("name", None):
            item["branch"] = branch_name.removeprefix(item.get("state", "") + "-")
        yield item
