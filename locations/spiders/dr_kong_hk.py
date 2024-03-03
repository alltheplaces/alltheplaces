from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class DrKongHKSpider(WPStoreLocatorSpider):
    days = DAYS_EN
    name = "dr_kong_hk"
    item_attributes = {
        "brand_wikidata": "Q116547631",
        "brand": "Dr. Kong",
    }
    allowed_domains = [
        "www.dr-kong.com.hk",
    ]
