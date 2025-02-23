from locations.hours import DAYS_ES
from locations.spiders.douglas_de import DouglasDESpider


class DouglasADESSpider(DouglasDESpider):
    name = "douglas_ad_es"
    allowed_domains = ["www.douglas.es"]
    start_urls = ["https://www.douglas.es/api/v2/stores?accuracy=0&currentPage=0&fields=FULL&pageSize=10000&sort=asc"]
    days = DAYS_ES
