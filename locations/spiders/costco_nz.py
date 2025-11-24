from locations.spiders.costco_au import CostcoAUSpider


class CostcoNZSpider(CostcoAUSpider):
    name = "costco_nz"
    allowed_domains = ["www.costco.co.nz"]
    start_urls = ["https://www.costco.co.nz/store-finder/search?q="]
