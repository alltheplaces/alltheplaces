from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class RoyalDonutsDESpider(WPStoreLocatorSpider):
    name = "royal_donuts_de"
    item_attributes = {
        "brand_wikidata": "Q112186115",
        "brand": "Royal Donuts",
    }
    allowed_domains = [
        "www.royal-donuts.de",
    ]
