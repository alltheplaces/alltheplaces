from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SuperverdESSpider(WPStoreLocatorSpider):
    name = "superverd_es"
    item_attributes = {
        "brand_wikidata": "Q11950546",
        "brand": "Superverd",
    }
    allowed_domains = [
        "www.superverd.es",
    ]
    start_urls = [
        "https://www.superverd.es/wp-admin/admin-ajax.php?action=store_search&lat=41.385064&lng=2.173404&autoload=1&distance_unit=km"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
