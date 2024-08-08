from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class PTerrysUSSpider(WPStoreLocatorSpider):
    name = "p_terrys_us"
    item_attributes = {
        "brand_wikidata": "Q19903521",
        "brand": "P. Terry's",
    }
    allowed_domains = [
        "pterrys.com",
    ]
    time_format = "%I:%M %p"
