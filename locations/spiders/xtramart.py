from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class XtraMartSpider(WPStoreLocatorSpider):
    name = "xtramart"
    item_attributes = {
        "brand_wikidata": "Q119586946",
        "brand": "XtraMart",
    }
    allowed_domains = [
        "xtramart.com",
    ]
    time_format = "%I:%M %p"
