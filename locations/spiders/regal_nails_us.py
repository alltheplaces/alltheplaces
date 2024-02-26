from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class RegalNailsUSSpider(WPStoreLocatorSpider):
    name = "regal_nails_us"
    item_attributes = {
        "brand_wikidata": "Q108918028",
        "brand": "Regal Nails",
    }
    allowed_domains = [
        "regalnails.com",
    ]
    start_urls = [
        "https://regalnails.com/wp-admin/admin-ajax.php?action=store_search&lat=30.4514677&lng=-91.18714659999999&max_results=1000&search_radius=1000&filter=10",
    ]
    time_format = "%I:%M %p"
