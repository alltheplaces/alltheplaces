from locations.spiders.costco_au import CostcoAUSpider


class CostcoMXSpider(CostcoAUSpider):
    name = "costco_mx"
    allowed_domains = ["www.costco.com.mx"]
    stores_url = (
        "https://www.costco.com.mx/rest/v2/mexico/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999"
    )
