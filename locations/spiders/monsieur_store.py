from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MonsieurStoreSpider(WPStoreLocatorSpider):
    name = "monsieur_store"
    item_attributes = {
        "brand_wikidata": "Q113686692",
        "brand": "Monsieur Store",
    }
    allowed_domains = [
        "monsieurstore.com",
    ]
