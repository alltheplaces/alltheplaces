from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SpeedyAutoServiceCASpider(WPStoreLocatorSpider):
    name = "speedy_auto_service_ca"
    item_attributes = {
        "brand_wikidata": "Q22318193",
        "brand": "Speedy Auto Service",
    }
    allowed_domains = [
        "www.speedy.com",
    ]
    time_format = "%I:%M %p"
