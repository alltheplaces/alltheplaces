from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class VanWallEquipmentCarroll(WPStoreLocatorSpider):
    name = "van_wall_equipment_carroll"
    item_attributes = {"brand": "Van Wall", "extras": Categories.SHOP_TOOL_HIRE.value}
    allowed_domains = [
        "vanwall.com",
    ]
    days = DAYS_EN