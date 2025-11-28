from locations.hours import DAYS_DE
from locations.spiders.douglas_de import DouglasDESpider


class DouglasCHSpider(DouglasDESpider):
    name = "douglas_ch"
    allowed_domains = ["www.douglas.ch"]
    start_urls = ["https://www.douglas.ch/api/v2/stores?accuracy=0&currentPage=0&fields=FULL&pageSize=10000&sort=asc"]
    days = DAYS_DE
