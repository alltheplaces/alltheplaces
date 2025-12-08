from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class PeluqueriasLowCostESSpider(AgileStoreLocatorSpider):
    name = "peluquerias_low_cost_es"
    item_attributes = {"brand": "Peluquería Low Cost", "brand_wikidata": "Q115775082"}
    allowed_domains = ["peluqueriaslowcost.com"]
