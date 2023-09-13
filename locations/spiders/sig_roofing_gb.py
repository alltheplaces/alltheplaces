from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SigRoofingGBSpider(WPStoreLocatorSpider):
    name = "sig_roofing_gb"
    item_attributes = {"brand": "SIG Roofing", "brand_wikidata": "Q121435383"}
    start_urls = [
        "https://www.sigroofing.co.uk/wp-admin/admin-ajax.php?action=store_search&lat=51.5072178&lng=-0.1275862&max_results=200&search_radius=500"
    ]
    time_format = "%I:%M %p"
