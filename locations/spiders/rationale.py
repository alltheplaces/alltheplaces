import re

from locations.categories import Categories, apply_category
from locations.storefinders.stockist import StockistSpider


class RationaleSpider(StockistSpider):
    name = "rationale"
    item_attributes = {"brand": "RATIONALE", "brand_wikidata": "Q119442596"}
    key = "u6176"

    def parse_item(self, item, location):
        for filter_type in location["filters"]:
            if filter_type["name"] == "Clinic Stockists":
                return
        if location.get("full_address"):
            item["addr_full"] = re.sub(r"\s+", " ", location["full_address"])
        apply_category(Categories.SHOP_COSMETICS, item)
        yield item
