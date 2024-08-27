from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BobablasticUSSpider(WPStoreLocatorSpider):
    name = "bobablastic_us"
    item_attributes = {
        "brand_wikidata": "Q108499280",
        "brand": "Bobablastic",
    }
    allowed_domains = [
        "bobablastic.com",
    ]
    time_format = "%I:%M %p"
