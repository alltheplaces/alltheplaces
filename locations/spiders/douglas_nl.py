from locations.hours import DAYS_NL
from locations.spiders.douglas_de import DouglasDESpider


class DouglasNLSpider(DouglasDESpider):
    name = "douglas_nl"
    allowed_domains = ["www.douglas.nl"]
    start_urls = ["https://www.douglas.nl/api/v2/stores?accuracy=0&currentPage=0&fields=FULL&pageSize=10000&sort=asc"]
    days = DAYS_NL
