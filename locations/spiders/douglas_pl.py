from locations.hours import DAYS_PL
from locations.spiders.douglas_de import DouglasDESpider


class DouglasPLSpider(DouglasDESpider):
    name = "douglas_pl"
    allowed_domains = ["www.douglas.pl"]
    start_urls = ["https://www.douglas.pl/api/v2/stores?accuracy=0&currentPage=0&fields=FULL&pageSize=10000&sort=asc"]
    days = DAYS_PL
