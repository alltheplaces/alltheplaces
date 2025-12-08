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
    custom_settings = {"ROBOTSTXT_OBEY": False}
