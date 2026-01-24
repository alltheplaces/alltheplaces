from typing import Iterable

from scrapy.http import Response

from locations.brand_utils import extract_located_in
from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.spiders.tom_wahls_us import TomWahlsUSSpider
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class AbbottsFrozenCustardUSSpider(WPStoreLocatorSpider):
    name = "abbotts_frozen_custard_us"
    item_attributes = {"brand": "Abbott's Frozen Custard", "brand_wikidata": "Q4664334"}
    allowed_domains = ["www.abbottscustard.com"]
    days = DAYS_EN

    LOCATED_IN_MAPPINGS = [
        (["bill-grays", "bill gray"], {"brand": "Bill Gray's", "brand_wikidata": "Q4909199"}),
        (["tom-wahls", "tom wahl"], TomWahlsUSSpider.item_attributes),
    ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")

        # All Abbott's locations are ice cream shops
        apply_category(Categories.ICE_CREAM, item)

        # Add parent venue information for locations inside other restaurants
        if branch := item.get("branch"):
            item["located_in"], item["located_in_wikidata"] = extract_located_in(branch, self.LOCATED_IN_MAPPINGS)
            if not item["located_in"] or not item["located_in_wikidata"]:
                if website := item.get("website"):
                    item["located_in"], item["located_in_wikidata"] = extract_located_in(website, self.LOCATED_IN_MAPPINGS)

        yield item
