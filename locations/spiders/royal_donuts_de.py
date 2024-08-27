from locations.categories import Categories
from locations.hours import DAYS_DE
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class RoyalDonutsDESpider(WPStoreLocatorSpider):
    name = "royal_donuts_de"
    item_attributes = {"brand_wikidata": "Q112186115", "brand": "Royal Donuts", "extras": Categories.FAST_FOOD.value}
    allowed_domains = [
        "www.royal-donuts.de",
    ]
    days = DAYS_DE
