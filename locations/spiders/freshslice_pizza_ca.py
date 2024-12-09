from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


# NOTE: Produces ~50 results; however coordinate based search only produes 45 results.
class FreshslicePizzaCASpider(WPStoreLocatorSpider):
    name = "freshslice_pizza_ca"
    item_attributes = {"brand_wikidata": "Q5503082", "brand": "Freshslice Pizza", "extras": Categories.FAST_FOOD.value}
    allowed_domains = [
        "www.freshslice.com",
    ]
    days = DAYS_EN
