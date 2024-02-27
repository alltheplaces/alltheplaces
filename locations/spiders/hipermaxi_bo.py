from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class HipermaxiBOSpider(AgileStoreLocatorSpider):
    name = "hipermaxi_bo"
    item_attributes = {
        "brand_wikidata": "Q81968262",
        "brand": "Hipermaxi",
    }
    allowed_domains = [
        "hipermaxi.com",
    ]
