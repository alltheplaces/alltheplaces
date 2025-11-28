from locations.hours import OpeningHours
from locations.spiders.costco_au import CostcoAUSpider


class CostcoISSpider(CostcoAUSpider):
    name = "costco_is"
    allowed_domains = ["www.costco.is"]
    start_urls = ["https://www.costco.is/store-finder/search?q="]

    def parse_hours_string(self, hours_string: str) -> OpeningHours:
        hours_string = hours_string.replace(".", "")
        return super().parse_hours_string(hours_string)
