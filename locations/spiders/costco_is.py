from locations.spiders.costco_au import CostcoAUSpider


class CostcoISSpider(CostcoAUSpider):
    name = "costco_is"
    allowed_domains = ["www.costco.is"]
    stores_url = (
        "https://www.costco.is/rest/v2/iceland/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999"
    )
