from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BricksMinifigsCAUSSpider(WPStoreLocatorSpider):
    name = "bricks_minifigs_ca_us"
    item_attributes = {
        "brand_wikidata": "Q109329121",
        "brand": "Bricks & Minifigs",
    }
    allowed_domains = [
        "bricksandminifigs.com",
    ]
    time_format = "%I:%M %p"
