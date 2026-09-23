from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.momentfeed import MomentFeedSpider


class AndysFrozenCustardUSSpider(MomentFeedSpider):
    name = "andys_frozen_custard_us"
    item_attributes = {"brand": "Andy's Frozen Custard", "brand_wikidata": "Q4760327"}
    api_key = "WYEMXMEMZMFGMIDG"

    def parse_item(self, item: Feature, feature: dict, store_info: dict) -> Iterable[Feature]:
        if store_info["status"] != "open":
            return
        if "Treat Truck" in item["name"] or "Home Office" in item["name"]:
            return
        item.pop("email", None)
        apply_category(Categories.ICE_CREAM, item)
        yield item
