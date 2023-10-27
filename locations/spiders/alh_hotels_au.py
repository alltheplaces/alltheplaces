from locations.categories import Categories, apply_category
from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class ALHHotelsAUAUSpider(StoreLocatorWidgetsSpider):
    name = "alh_hotels_au"
    item_attributes = {"brand": "ALH Hotels", "brand_wikidata": "Q119159708"}
    key = "41fdc8f98fc2738172250baa676b369d"

    def parse_item(self, item, location):
        if "hotel" in item["name"].lower() or "inn" in item["name"].lower():
            apply_category(Categories.HOTEL, item)
        elif "tavern" in item["name"].lower():
            apply_category(Categories.RESTAURANT, item)
        elif "pub" in item["name"].lower() or "grill" in item["name"].lower():
            apply_category(Categories.PUB, item)
        elif "bar" in item["name"].lower():
            apply_category(Categories.BAR, item)
        elif "cafe" in item["name"].lower():
            apply_category(Categories.CAFE, item)
        yield item
