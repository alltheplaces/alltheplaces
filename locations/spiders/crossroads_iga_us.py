from locations.categories import Categories, apply_category
from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class CrossroadsIgaUSSpider(StoreLocatorWidgetsSpider):
    name = "crossroads_iga_us"
    item_attributes = {"brand": "Crossroads IGA", "brand_wikidata": "Q119141723"}
    key = "8fd8a5ddd08a378ebba22cc2c9dce74f"

    def parse_item(self, item, location):
        item.pop("website")
        if location.get("filters"):
            if "Groceries" in location["filters"]:
                apply_category(Categories.SHOP_SUPERMARKET, item)
            if "Fuel" in location["filters"]:
                apply_category(Categories.FUEL_STATION, item)
        else:
            apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
