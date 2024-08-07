from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class TheAthletesFootSpider(WPStoreLocatorSpider):
    name = "the_athletes_foot"
    item_attributes = {
        "brand_wikidata": "Q7714792",
        "brand": "The Athlete's Foot",
    }
    allowed_domains = [
        "www.theathletesfoot.com",
    ]
    search_radius = 200
    max_results = 50
    searchable_points_files = ["earth_centroids_iseadgg_346km_radius.csv"]
