import re

from locations.hours import OpeningHours, DAYS_KR
from locations.spiders.costco_au import CostcoAUSpider


class CostcoKRSpider(CostcoAUSpider):
    name = "costco_kr"
    allowed_domains = ["www.costco.co.kr"]
    start_urls = ["https://www.costco.co.kr/store-finder/search?q="]
    day_labels = DAYS_KR

    def parse_hours_string(self, hours_string: str) -> OpeningHours:
        hours_string = re.sub(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", r"\1AM - \2PM", hours_string.replace("오전", "").replace("오후", ""))
        return super().parse_hours_string(hours_string)
