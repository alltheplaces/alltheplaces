from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MrPriceIESpider(WPStoreLocatorSpider):
    name = "mr_price_ie"
    item_attributes = {
        "brand_wikidata": "Q113197454",
        "brand": "Mr. Price",
    }
    allowed_domains = [
        "www.mrprice.ie",
    ]
    time_format = "%I:%M %p"
    start_urls = [
        "https://www.mrprice.ie/wp-admin/admin-ajax.php?action=store_search&lat=53.34981&lng=-6.26031&max_results=5000&search_radius=5000"
    ]
