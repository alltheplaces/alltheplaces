from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class UsaveGBSpider(WPStoreLocatorSpider):
    name = "usave_gb"
    item_attributes = {"brand_wikidata": "Q121435010", "brand": "USave", "extras": Categories.SHOP_CONVENIENCE.value}
    allowed_domains = [
        "www.usave.org.uk",
    ]
    days = DAYS_EN
