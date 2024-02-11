from locations.categories import Categories
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BilgroDESpider(WPStoreLocatorSpider):
    name = "bilgro_de"
    item_attributes = {"brand_wikidata": "Q108029888", "brand": "bilgro", "extras": Categories.SHOP_BEVERAGES.value}
    allowed_domains = [
        "www.bilgro.de",
    ]
    start_urls = [
        "https://www.bilgro.de/wp-admin/admin-ajax.php?action=store_search&lat=50.969454&lng=13.122099&max_results=1000&search_radius=10000&autoload=1"
    ]
