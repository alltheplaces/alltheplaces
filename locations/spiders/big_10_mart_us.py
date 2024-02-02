import re

from locations.categories import Categories, apply_category
from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class Big10MartUSSpider(StoreLocatorWidgetsSpider):
    name = "big_10_mart_us"
    item_attributes = {"brand": "Big 10 Mart", "brand_wikidata": "Q116867087"}
    key = "9ffd00cbcc632fa325a2f848806d57e2"

    def parse_item(self, item, location: {}, **kwargs):
        if m := re.search(r"#(\d+)", item["name"]):
            item["ref"] = m.group(1)
        item["addr_full"] = " ".join(item["addr_full"].split())
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
