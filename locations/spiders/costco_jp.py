import re

from locations.hours import DAYS_EN, DAYS_JP, OpeningHours
from locations.spiders.costco_au import CostcoAUSpider


class CostcoJPSpider(CostcoAUSpider):
    name = "costco_jp"
    allowed_domains = ["www.costco.co.jp"]
    start_urls = ["https://www.costco.co.jp/store-finder/search?q="]
    day_labels = DAYS_JP | DAYS_EN

    def parse_hours_string(self, hours_string: str) -> OpeningHours:
        if re.match("^\s*\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}(?!\d)", hours_string):
            hours_string = f"月曜日 - 日曜日: {hours_string}"
        return super().parse_hours_string(hours_string)
