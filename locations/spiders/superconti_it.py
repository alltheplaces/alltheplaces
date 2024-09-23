from locations.categories import Categories
from locations.hours import DAYS_IT
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SupercontiITSpider(WPStoreLocatorSpider):
    name = "superconti_it"
    item_attributes = {
        "brand": "Superconti",
        "brand_wikidata": "Q69381940",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    allowed_domains = ["www.superconti.eu"]
    days = DAYS_IT
