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
    start_urls = [
        "https://buffaloexchange.com/wp-admin/admin-ajax.php?action=store_search&lat=38.19447&lng=-95.74276&max_results=1000&search_radius=1000"
    ]
