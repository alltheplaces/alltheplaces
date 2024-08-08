from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class UsaveGBSpider(WPStoreLocatorSpider):
    name = "usave_gb"
    item_attributes = {
        "brand_wikidata": "Q121435010",
        "brand": "USave",
    }
    allowed_domains = [
        "www.usave.org.uk",
    ]
    time_format = "%I:%M %p"
