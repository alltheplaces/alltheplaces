from locations.hours import CLOSED_ES, DAYS_ES, DELIMITERS_ES
from locations.spiders.costco_au import CostcoAUSpider


class CostcoESSpider(CostcoAUSpider):
    name = "costco_es"
    allowed_domains = ["www.costco.es"]
    start_urls = ["https://www.costco.es/store-finder/search?q="]
    day_labels = DAYS_ES
    delimiters = DELIMITERS_ES
    closed_labels = CLOSED_ES
