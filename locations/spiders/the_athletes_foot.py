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
