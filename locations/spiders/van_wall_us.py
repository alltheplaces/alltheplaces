from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class VanWallUSSpider(WPStoreLocatorSpider):
    name = "van_wall_us"
    item_attributes = {"brand": "Van Wall", "extras": Categories.SHOP_PLANT_HIRE.value}
    allowed_domains = [
        "vanwall.com",
    ]
    days = DAYS_EN
