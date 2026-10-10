from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class XtramartUSSpider(WPStoreLocatorSpider):
    name = "xtramart_us"
    item_attributes = {"brand": "XtraMart", "brand_wikidata": "Q119586946"}
    allowed_domains = ["xtramart.com"]
    days = DAYS_EN
