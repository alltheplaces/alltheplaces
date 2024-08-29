from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BusyBeaverUSSpider(WPStoreLocatorSpider):
    name = "busy_beaver_us"
    item_attributes = {
        "brand": "Busy Beaver",
        "brand_wikidata": "Q108394482",
        "extras": Categories.SHOP_DOITYOURSELF.value,
    }
    allowed_domains = ["busybeaver.com"]
    days = DAYS_EN
