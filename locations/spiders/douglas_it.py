from locations.hours import DAYS_IT
from locations.spiders.douglas_de import DouglasDESpider


class DouglasITSpider(DouglasDESpider):
    name = "douglas_it"
    allowed_domains = ["www.douglas.it"]
    start_urls = ["https://www.douglas.it/api/v2/stores?accuracy=0&currentPage=0&fields=FULL&pageSize=10000&sort=asc"]
    days = DAYS_IT
