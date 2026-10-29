from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class ReformhausBacherDESpider(WPStoreLocatorSpider):
    name = "reformhaus_bacher_de"
    item_attributes = {
        "brand_wikidata": "Q19816424",
        "brand": "Reformhaus Bacher",
        "extras": Categories.SHOP_HEALTH_FOOD.value,
    }
    allowed_domains = [
        "www.reformhaus-bacher.de",
    ]
    days = DAYS_EN
    start_urls = [
        "https://www.reformhaus-bacher.de/wp-admin/admin-ajax.php?action=store_search&lat=51.165691&lng=10.451526&max_results=200&search_radius=10000&distance_unit=km"
    ]
