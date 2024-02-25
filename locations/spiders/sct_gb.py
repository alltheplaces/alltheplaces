from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SCTGBSpider(WPStoreLocatorSpider):
    name = "sct_gb"
    item_attributes = {
        "brand_wikidata": "Q107463316",
        "brand": "Spitalfields Crypt Trust",
    }
    allowed_domains = [
        "www.sct.org.uk",
    ]
    time_format = "%I:%M %p"
