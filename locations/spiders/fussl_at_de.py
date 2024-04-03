from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class FusslATDESpider(AgileStoreLocatorSpider):
    name = "fussl_at_de"
    item_attributes = {
        "brand_wikidata": "Q24266366",
        "brand": "Fussl",
    }
    allowed_domains = [
        "www.fussl.at",
    ]
