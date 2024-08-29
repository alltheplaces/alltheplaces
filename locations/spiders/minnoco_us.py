from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MinnocoUSSpider(WPStoreLocatorSpider):
    name = "minnoco_us"
    item_attributes = {"brand": "Minnoco", "extras": Categories.FUEL_STATION.value}
    allowed_domains = ["minnoco.com"]
    days = DAYS_EN
