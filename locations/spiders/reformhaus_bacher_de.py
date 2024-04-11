from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class ReformhausBacherDESpider(WPStoreLocatorSpider):
    name = "reformhaus_bacher_de"
    item_attributes = {
        "brand_wikidata": "Q19816424",
        "brand": "Reformhaus Bacher",
    }
    allowed_domains = [
        "www.reformhaus-bacher.de",
    ]
