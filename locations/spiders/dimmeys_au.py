from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class DimmeysAUSpider(AgileStoreLocatorSpider):
    name = "dimmeys_au"
    item_attributes = {
        "brand_wikidata": "Q17003075",
        "brand": "Dimmeys",
    }
    allowed_domains = [
        "www.dimmeys.com.au",
    ]
