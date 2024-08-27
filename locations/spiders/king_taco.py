from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class KingTacoSpider(WPStoreLocatorSpider):
    name = "king_taco"
    item_attributes = {
        "brand_wikidata": "Q6412104",
        "brand": "King Taco",
    }
    allowed_domains = [
        "kingtaco.com",
    ]
    time_format = "%I:%M %p"
