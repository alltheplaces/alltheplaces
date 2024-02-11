from locations.categories import Categories
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class CycleSpotJPSpider(WPStoreLocatorSpider):
    name = "cycle_spot_jp"
    item_attributes = {
        "brand_wikidata": "Q93620124",
        "brand": "サイクルスポット",
        "extras": Categories.SHOP_BICYCLE.value,
    }
    allowed_domains = [
        "www.cyclespot.net",
    ]
    start_urls = (
        "https://www.cyclespot.net/wp-admin/admin-ajax.php?action=store_search&autoload=1&max_results=1000&search_radius=10000",
    )
