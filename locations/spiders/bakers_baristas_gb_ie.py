from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class BakersBaristasGBIESpider(AgileStoreLocatorSpider):
    name = "bakers_baristas_gb_ie"
    item_attributes = {
        "brand_wikidata": "Q85199581",
        "brand": "Bakers + Baristas",
    }
    allowed_domains = [
        "www.bakersbaristas.com",
    ]
