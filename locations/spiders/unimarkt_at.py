from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class UnimarktATSpider(WPStoreLocatorSpider):
    name = "unimarkt_at"
    item_attributes = {
        "brand_wikidata": "Q1169599",
        "brand": "Unimarkt",
    }
    allowed_domains = [
        "unimarkt.at",
    ]
