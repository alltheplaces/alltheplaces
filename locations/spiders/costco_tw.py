import re

from locations.hours import OpeningHours, DAYS_CN
from locations.spiders.costco_au import CostcoAUSpider


class CostcoTWSpider(CostcoAUSpider):
    name = "costco_tw"
    allowed_domains = ["www.costco.com.tw"]
    start_urls = ["https://www.costco.com.tw/store-finder/search?q="]
    day_labels = DAYS_CN

    def parse_hours_string(self, hours_string: str) -> OpeningHours:
        hours_string = re.sub(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", r"\1AM - \2PM", hours_string.replace("上午", "").replace("下午", "").replace("~", " - "))
        return super().parse_hours_string(hours_string)
