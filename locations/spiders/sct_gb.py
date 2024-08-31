from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SctGBSpider(WPStoreLocatorSpider):
    name = "sct_gb"
    item_attributes = {
        "brand_wikidata": "Q107463316",
        "brand": "Spitalfields Crypt Trust",
        "extras": Categories.SHOP_CHARITY.value,
    }
    allowed_domains = [
        "www.sct.org.uk",
    ]
    days = DAYS_EN
