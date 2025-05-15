from locations.hours import DAYS_SK
from locations.spiders.douglas_de import DouglasDESpider


class DouglasSKSpider(DouglasDESpider):
    name = "douglas_sk"
    allowed_domains = ["www.douglas.sk"]
    start_urls = ["https://www.douglas.sk/api/v2/stores?accuracy=0&currentPage=0&fields=FULL&pageSize=10000&sort=asc"]
    days = DAYS_SK
