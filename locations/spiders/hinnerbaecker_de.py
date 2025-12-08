from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class HinnerbaeckerDESpider(AgileStoreLocatorSpider):
    name = "hinnerbaecker_de"
    item_attributes = {
        "brand_wikidata": "Q107985183",
        "brand": "Hinnerbäcker",
    }
    allowed_domains = [
        "hinnerbaecker.com",
    ]
