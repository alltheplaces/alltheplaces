from locations.categories import Categories
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BusyBeaverSpider(WPStoreLocatorSpider):
    name = "busy_beaver"
    item_attributes = {
        "brand": "Busy Beaver",
        "brand_wikidata": "Q108394482",
        "extras": Categories.SHOP_DOITYOURSELF.value,
    }
    allowed_domains = ["busybeaver.com"]
    time_format = "%I:%M %p"
