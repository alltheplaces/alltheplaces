from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class HosselmannDESpider(WPStoreLocatorSpider):
    name = "hosselmann_de"
    item_attributes = {
        "brand_wikidata": "Q107203160",
        "brand": "Hosselmann",
    }
    allowed_domains = [
        "hosselmann.de",
    ]
