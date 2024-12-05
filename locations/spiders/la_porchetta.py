from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class LaPorchettaSpider(WPStoreLocatorSpider):
    name = "la_porchetta"
    item_attributes = {"brand": "La Porchetta", "brand_wikidata": "Q6464528"}
    start_urls = ["https://laporchetta.com.au/wp-admin/admin-ajax.php?action=store_search&autoload=1"]
