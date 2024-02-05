import re

from locations.categories import Categories, apply_category
from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class BlackRoosterPeriPeriGBSpider(StoreLocatorWidgetsSpider):
    name = "black_rooster_peri_peri_gb"
    item_attributes = {"brand": "Black Rooster Peri Peri", "brand_wikidata": "Q119158787"}
    key = "d9fa8573a1f38aee44860f511a67e368"

    def parse_item(self, item, location):
        item["name"] = item["name"].strip()
        item["addr_full"] = re.sub(r"\s+", " ", item["addr_full"])
        item.pop("website")
        apply_category(Categories.FAST_FOOD, item)
        yield item
