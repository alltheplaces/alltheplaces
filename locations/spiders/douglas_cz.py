from locations.hours import DAYS_CZ
from locations.spiders.douglas_de import DouglasDESpider


class DouglasCZSpider(DouglasDESpider):
    name = "douglas_cz"
    allowed_domains = ["www.douglas.cz"]
    start_urls = ["https://www.douglas.cz/api/v2/stores?accuracy=0&currentPage=0&fields=FULL&pageSize=10000&sort=asc"]
    days = DAYS_CZ
