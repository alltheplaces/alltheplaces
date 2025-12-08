from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class SuperBioMarktDESpider(AgileStoreLocatorSpider):
    name = "super_bio_markt_de"
    item_attributes = {
        "brand_wikidata": "Q2367009",
        "brand": "SuperBioMarkt",
    }
    allowed_domains = [
        "www.superbiomarkt.de",
    ]
