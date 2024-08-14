from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class UfsAUSpider(WPStoreLocatorSpider):
    name = "ufs_au"
    item_attributes = {"brand": "UFS", "brand_wikidata": "Q63367573"}
    allowed_domains = ["www.ufs.com.au"]
    start_urls = ["https://www.ufs.com.au/ufs1/wp-admin/admin-ajax.php?action=store_search&autoload=1"]
