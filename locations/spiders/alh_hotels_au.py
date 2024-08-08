from locations.categories import Categories, apply_category
from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class AlhHotelsAUSpider(StoreLocatorWidgetsSpider):
    name = "alh_hotels_au"
    item_attributes = {"brand": "ALH Hotels", "brand_wikidata": "Q119159708"}
    key = "41fdc8f98fc2738172250baa676b369d"

    def parse_item(self, item, location):
        item_name = item["name"].lower()
        if "hotel" in item_name or "inn" in item_name:
            apply_category(Categories.HOTEL, item)
        elif "tavern" in item_name:
            apply_category(Categories.RESTAURANT, item)
        elif "pub" in item_name or "grill" in item_name:
            apply_category(Categories.PUB, item)
        elif "bar" in item_name:
            apply_category(Categories.BAR, item)
        elif "cafe" in item_name:
            apply_category(Categories.CAFE, item)
        yield item
