from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class TheAthletesFootSpider(WPStoreLocatorSpider):
    name = "the_athletes_foot"
    item_attributes = {
        "brand_wikidata": "Q7714792",
        "brand": "The Athlete's Foot",
        "extras": Categories.SHOP_SHOES.value,
    }
    allowed_domains = [
        "www.theathletesfoot.com",
    ]
    searchable_points_files = ["earth_centroids_iseadgg_346km_radius.csv"]
    search_radius = 200
    max_results = 50
    days = DAYS_EN
