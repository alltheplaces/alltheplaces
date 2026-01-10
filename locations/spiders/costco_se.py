from locations.spiders.costco_au import CostcoAUSpider


class CostcoSESpider(CostcoAUSpider):
    name = "costco_se"
    allowed_domains = ["www.costco.se"]
    stores_url = (
        "https://www.costco.se/rest/v2/sweden/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999"
    )
