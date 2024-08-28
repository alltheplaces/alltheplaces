from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class AlltownFreshUSSpider(WPStoreLocatorSpider):
    name = "alltown_fresh_us"
    item_attributes = {
        "brand_wikidata": "Q119591365",
        "brand": "Alltown Fresh",
        "extras": Categories.SHOP_CONVENIENCE.value,
    }
    allowed_domains = [
        "alltownfresh.com",
    ]
    days = DAYS_EN
