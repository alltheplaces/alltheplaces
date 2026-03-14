from locations.hours import DAYS_AT
from locations.spiders.douglas_de import DouglasDESpider


class DouglasATSpider(DouglasDESpider):
    name = "douglas_at"
    allowed_domains = ["www.douglas.at"]
    start_urls = ["https://www.douglas.at/api/v2/stores?accuracy=0&currentPage=0&fields=FULL&pageSize=10000&sort=asc"]
    days = DAYS_AT
