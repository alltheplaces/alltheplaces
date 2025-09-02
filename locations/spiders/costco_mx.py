
from locations.hours import CLOSED_ES, DAYS_ES, DELIMITERS_ES, OpeningHours
from locations.spiders.costco_au import CostcoAUSpider


class CostcoMXSpider(CostcoAUSpider):
    name = "costco_mx"
    allowed_domains = ["www.costco.com.mx"]
    start_urls = ["https://www.costco.com.mx/store-finder/search?q="]
    day_labels = DAYS_ES
    delimiters = DELIMITERS_ES
    closed_labels = CLOSED_ES

    def parse_hours_string(self, hours_string: str) -> OpeningHours:
        hours_string = hours_string.replace("a.m.", "AM").replace("p.m.", "PM")
        return super().parse_hours_string(hours_string)
