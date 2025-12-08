from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class JiffyMartUSSpider(WPStoreLocatorSpider):
    name = "jiffy_mart_us"
    item_attributes = {
        "brand_wikidata": "Q119592174",
        "brand": "Jiffy Mart",
        "extras": Categories.SHOP_CONVENIENCE.value,
    }
    allowed_domains = [
        "jiffymartstores.com",
    ]
    days = DAYS_EN
