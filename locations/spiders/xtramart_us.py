from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class XtramartUSSpider(WPStoreLocatorSpider):
    name = "xtramart_us"
    item_attributes = {"brand_wikidata": "Q119586946", "brand": "XtraMart", "extras": Categories.SHOP_CONVENIENCE.value}
    allowed_domains = [
        "xtramart.com",
    ]
    days = DAYS_EN
