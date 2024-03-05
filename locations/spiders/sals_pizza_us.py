import re

from locations.categories import Categories
from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class SalsPizzaUSSpider(StoreLocatorWidgetsSpider):
    name = "sals_pizza_us"
    item_attributes = {"brand": "Sal's Pizza", "brand_wikidata": "Q7403249", "extras": Categories.RESTAURANT.value}
    key = "178ecac2bff5d20c4041ada5f817d79e"

    def parse_item(self, item, location):
        if "Sals" not in location["filters"]:
            return
        item["addr_full"] = re.sub(r"\s+", " ", item["addr_full"])
        item.pop("website")
        yield item
