from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class VanWallUSSpider(WPStoreLocatorSpider):
    item_attributes = {"brand": "Van Wall", "extras": Categories.SHOP_PLANT_HIRE.value}
    days = DAYS_EN
    name = "van_wall_us"
    allowed_domains = [
        "vanwall.com",
    ]
    time_format = "%I:%M %p"
