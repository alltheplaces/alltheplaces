from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class BufkesNLSpider(AgileStoreLocatorSpider):
    name = "bufkes_nl"
    item_attributes = {"brand": "Bufkes", "brand_wikidata": "Q124348748"}
    allowed_domains = ["bufkes.nl"]
