from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class AlltownFreshUSSpider(WPStoreLocatorSpider):
    name = "alltown_fresh_us"
    item_attributes = {
        "brand_wikidata": "Q119591365",
        "brand": "Alltown Fresh",
    }
    allowed_domains = [
        "alltownfresh.com",
    ]
    time_format = "%I:%M %p"
