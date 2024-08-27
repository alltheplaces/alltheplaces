from locations.categories import Categories
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider

from locations.hours import.DAYS_EN


class FreshslicePizzaCASpider(WPStoreLocatorSpider):
    name = "freshslice_pizza_ca"
    item_attributes = {
        "brand_wikidata": "Q5503082",
        "brand": "Freshslice Pizza",
        "extras": Categories.FAST_FOOD.value
    }
    allowed_domains = [
        "www.freshslice.com",
    ]
    time_format = "%I:%M %p"
    days = DAYS_EN
