from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class PretzelmakerUSSpider(WPStoreLocatorSpider):
    name = "pretzelmaker_us"
    item_attributes = {
        "brand_wikidata": "Q7242321",
        "brand": "Pretzelmaker",
    }
    allowed_domains = [
        "www.pretzelmaker.com",
    ]
    time_format = "%I:%M %p"
