from locations.hours import DAYS_NL
from locations.spiders.douglas_de import DouglasDESpider


class DouglasBESpider(DouglasDESpider):
    name = "douglas_be"
    allowed_domains = ["www.douglas.be"]
    start_urls = ["https://www.douglas.be/api/v2/stores?accuracy=0&currentPage=0&fields=FULL&pageSize=10000&sort=asc"]
    days = DAYS_NL
