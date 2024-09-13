from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class KitchenConnectionAUSpider(WPStoreLocatorSpider):
    name = "kitchen_connection_au"
    item_attributes = {
        "brand_wikidata": "Q111081406",
        "brand": "Kitchen Connection",
        "extras": Categories.SHOP_KITCHEN.value,
    }
    allowed_domains = [
        "kitchenconnection.com.au",
    ]
    days = DAYS_EN
