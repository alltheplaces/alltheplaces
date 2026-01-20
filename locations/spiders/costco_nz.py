from locations.spiders.costco_au import CostcoAUSpider


class CostcoNZSpider(CostcoAUSpider):
    name = "costco_nz"
    allowed_domains = ["www.costco.co.nz"]
    stores_url = "https://www.costco.co.nz/rest/v2/newzealand/stores?fields=FULL&radius=3000000&returnAllStores=true&pageSize=999"
