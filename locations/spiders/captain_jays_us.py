from locations.categories import Categories
from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class CaptainJaysUSSpider(StoreLocatorWidgetsSpider):
    name = "captain_jays_us"
    item_attributes = {
        "brand": "Captain Jay's",
        "brand_wikidata": "Q119157361",
        "extras": Categories.RESTAURANT.value,
    }
    key = "3c3dd9d2b7bc80dce3f32d4985d28d5a"
