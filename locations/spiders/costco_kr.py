from locations.spiders.costco_au import CostcoAUSpider


class CostcoKRSpider(CostcoAUSpider):
    name = "costco_kr"
    allowed_domains = ["www.costco.co.kr"]
    stores_url = (
        "https://www.costco.co.kr/rest/v2/korea/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999"
    )
