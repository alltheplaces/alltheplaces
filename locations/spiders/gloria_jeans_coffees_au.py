from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class GloriaJeansCoffeesAUSpider(WPStoreLocatorSpider):
    name = "gloria_jeans_coffees_au"
    item_attributes = {"brand": "Gloria Jean's Coffees", "brand_wikidata": "Q2666365"}
    start_urls = ["https://www.gloriajeanscoffees.com.au/wp/wp-admin/admin-ajax.php?action=store_search"]
    iseadgg_countries_list = ["AU"]
    search_radius = 50
    max_results = 50
    days = DAYS_EN
