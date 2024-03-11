from locations.categories import Categories
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class PeluqueriasLowCostESSpider(AgileStoreLocatorSpider):
    name = "peluquerias_low_cost_es"
    item_attributes = {
        "brand": "Peluquerías Low Cost",
        "brand_wikidata": "Q115775082",
        "extras": Categories.SHOP_HAIRDRESSER.value,
    }
    allowed_domains = ["peluqueriaslowcost.com"]
