from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class AbbottsFrozenCustardUSSpider(WPStoreLocatorSpider):
    name = "abbotts_frozen_custard_us"
    item_attributes = {"brand": "Abbott's Frozen Custard", "brand_wikidata": "Q4664334"}
    allowed_domains = ["www.abbottscustard.com"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")

        # All Abbott's locations are ice cream shops
        apply_category(Categories.ICE_CREAM, item)

        # Add parent venue information for locations inside other restaurants
        self._set_located_in(item)

        yield item

    def _set_located_in(self, item):
        """Set parent venue information for locations inside other restaurants"""
        ref = item["website"].lower()
        name_lower = item.get("branch", "").lower()

        if "bill-grays" in ref or "bill gray" in name_lower:
            item["located_in"] = "Bill Gray's"
            item["located_in_wikidata"] = "Q4909199"
        elif "tom-wahls" in ref or "tom wahl" in name_lower:
            item["located_in"] = "Tom Wahl's"
            item["located_in_wikidata"] = "Q7817965"
