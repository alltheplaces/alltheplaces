from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class DrakesAUSpider(WPStoreLocatorSpider):
    name = "drakes_au"
    item_attributes = {"brand_wikidata": "Q48988077", "brand": "Drakes", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = [
        "drakes.com.au",
    ]
    start_urls = [
        "https://drakes.com.au/wp-admin/admin-ajax.php?action=store_search&lat=-34.928499&lng=138.600746&max_results=100&search_radius=500"
    ]
    days = DAYS_EN
