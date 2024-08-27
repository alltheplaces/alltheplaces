from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class ProcolorCollisionUSSpider(WPStoreLocatorSpider):
    name = "procolor_collision_us"
    item_attributes = {
        "brand_wikidata": "Q120648778",
        "brand": "ProColor Collision",
        "extras": Categories.SHOP_CAR_REPAIR.value,
    }
    allowed_domains = [
        "www.procolor.com",
    ]
    days = DAYS_EN
