from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class AmatosSpider(WPStoreLocatorSpider):
    name = "amatos"
    item_attributes = {
        "brand_wikidata": "Q4740614",
        "brand": "Amato's",
    }
    allowed_domains = [
        "www.amatos.com",
    ]
