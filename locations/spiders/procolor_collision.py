from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class ProcolorCollisionSpider(WPStoreLocatorSpider):
    name = "procolor_collision"
    item_attributes = {
        "brand_wikidata": "Q120648778",
        "brand": "ProColor Collision",
    }
    allowed_domains = [
        "www.procolor.com",
    ]
    time_format = "%I:%M %p"
