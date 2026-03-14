from locations.spiders.costco_au import CostcoAUSpider


class CostcoESSpider(CostcoAUSpider):
    name = "costco_es"
    allowed_domains = ["www.costco.es"]
    stores_url = (
        "https://www.costco.es/rest/v2/spain/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999"
    )
