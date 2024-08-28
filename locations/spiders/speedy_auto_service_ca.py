from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SpeedyAutoServiceCASpider(WPStoreLocatorSpider):
    name = "speedy_auto_service_ca"
    item_attributes = {
        "brand_wikidata": "Q22318193",
        "brand": "Speedy Auto Service",
        "extras": Categories.SHOP_CAR_REPAIR.value,
    }
    allowed_domains = [
        "www.speedy.com",
    ]
    days = DAYS_EN
