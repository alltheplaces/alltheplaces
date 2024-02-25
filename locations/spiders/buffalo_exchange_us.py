from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BuffaloExchangeUSSpider(WPStoreLocatorSpider):
    name = "buffalo_exchange_us"
    item_attributes = {
        "brand_wikidata": "Q4985721",
        "brand": "Buffalo Exchange",
    }
    allowed_domains = [
        "buffaloexchange.com",
    ]
    time_format = "%I:%M %p"
