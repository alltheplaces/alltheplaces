from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class ShawarmerSASpider(WPStoreLocatorSpider):
    name = "shawarmer_sa"
    item_attributes = {
        "brand_wikidata": "Q29509653",
        "brand": "شاورمر",
    }
    allowed_domains = [
        "www.shawarmer.com",
    ]
