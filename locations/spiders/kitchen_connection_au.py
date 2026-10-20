from locations.categories import Categories
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class KitchenConnectionAUSpider(WPStoreLocatorSpider):
    name = "kitchen_connection_au"
    item_attributes = {
        "brand_wikidata": "Q111081406",
        "brand": "Kitchen Connection",
        "extras": Categories.SHOP_KITCHEN.value,
    }
    start_urls = [
        "https://kitchenconnection.com.au/wp-admin/admin-ajax.php?action=store_search&lat=-27.470453&lng=153.026034&max_results=100&search_radius=100&distance_unit=km"
    ]
