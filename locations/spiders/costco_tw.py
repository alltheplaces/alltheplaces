from locations.spiders.costco_au import CostcoAUSpider


class CostcoTWSpider(CostcoAUSpider):
    name = "costco_tw"
    allowed_domains = ["www.costco.com.tw"]
    stores_url = (
        "https://www.costco.com.tw/rest/v2/taiwan/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999"
    )
