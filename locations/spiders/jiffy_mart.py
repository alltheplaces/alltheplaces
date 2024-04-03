from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class JiffyMartSpider(WPStoreLocatorSpider):
    name = "jiffy_mart"
    item_attributes = {
        "brand_wikidata": "Q119592174",
        "brand": "Jiffy Mart",
    }
    allowed_domains = [
        "jiffymartstores.com",
    ]
    time_format = "%I:%M %p"
    days = DAYS_EN
