from locations.hours import CLOSED_SE, DAYS_SE
from locations.spiders.costco_au import CostcoAUSpider


class CostcoSESpider(CostcoAUSpider):
    name = "costco_se"
    allowed_domains = ["www.costco.se"]
    start_urls = ["https://www.costco.se/store-finder/search?q="]
    day_labels = DAYS_SE
    closed_labels = CLOSED_SE
