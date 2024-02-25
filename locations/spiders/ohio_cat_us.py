from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class OhioCATUSSpider(WPStoreLocatorSpider):
    name = "ohio_cat_us"
    item_attributes = {
        "brand_wikidata": "Q115486235",
        "brand": "Ohio CAT",
    }
    allowed_domains = [
        "ohiocat.com",
    ]
    time_format = "%I:%M %p"
