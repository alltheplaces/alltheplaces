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
        "sct.org.uk",
    ]
    days = DAYS_EN
    start_urls = [
        "https://sct.org.uk/wp-admin/admin-ajax.php?action=store_search&lat=51.507218&lng=-0.127586&max_results=100&search_radius=1000"
    ]
