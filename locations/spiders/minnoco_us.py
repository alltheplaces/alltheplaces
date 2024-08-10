from locations.categories import Categories
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MinnocoUSSpider(WPStoreLocatorSpider):
    name = "minnoco_us"
    item_attributes = {"brand": "Minnoco", "extras": Categories.FUEL_STATION.value}
    allowed_domains = ["minnoco.com"]
    start_urls = ["https://www.minnoco.com/wp-admin/admin-ajax.php?action=store_search&autoload=1"]
    time_format = "%I:%M %p"
