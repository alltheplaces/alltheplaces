from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class AlltownUSSpider(WPStoreLocatorSpider):
    name = "alltown_us"
    item_attributes = {"brand_wikidata": "Q119586667", "brand": "Alltown", "extras": Categories.SHOP_CONVENIENCE.value}
    allowed_domains = [
        "alltown.com",
    ]
    days = DAYS_EN
