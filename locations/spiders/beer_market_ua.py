import re
from ast import literal_eval
from hashlib import sha1

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_RU, OpeningHours, day_range
from locations.items import Feature

# Ukrainian abbreviation for Sunday not covered by DAYS_RU.
DAYS_MAP = {**DAYS_RU, "Нд": "Su"}

PLACEMARK_PATTERN = re.compile(r"BX_GMapAddPlacemark\((\{.*?\}), '\w+'\);")
FIELD_PATTERN = re.compile(r'<div class="(\w)">(.*?)<\\/div>', re.S)


class BeerMarketUASpider(Spider):
    name = "beer_market_ua"
    item_attributes = {"brand": "Beer Market", "brand_wikidata": "Q119202199"}
    allowed_domains = ["beer-market.com.ua"]
    start_urls = ["https://www.beer-market.com.ua/"]

    def parse(self, response: Response):
        for match in PLACEMARK_PATTERN.findall(response.text):
            placemark = literal_eval(match)
            fields = dict(FIELD_PATTERN.findall(placemark["TEXT"]))

            address = fields.get("l", "").replace("\\/", "/").strip()
            if not address:
                continue

            item = Feature()
            item["ref"] = sha1(f"{address}|{placemark['LAT']}|{placemark['LON']}".encode("utf-8")).hexdigest()
            item["lat"] = placemark["LAT"]
            item["lon"] = placemark["LON"]
            item["addr_full"] = address
            item["country"] = "UA"
            item["website"] = response.url

            if hours := fields.get("t"):
                item["opening_hours"] = self.parse_hours(hours)

            apply_category(Categories.SHOP_ALCOHOL, item)

            yield item

    @staticmethod
    def parse_hours(text: str) -> OpeningHours:
        oh = OpeningHours()
        for line in text.replace("\\n", "\n").strip().split("\n"):
            line = line.strip()
            if m := re.match(r"^(.*?)\s+(\d{1,2})-(\d{1,2})\s*$", line):
                days_part, start, end = m.groups()
                for group in days_part.split(","):
                    group = group.strip()
                    if "-" in group:
                        day_from, day_to = [DAYS_MAP[d.strip()] for d in group.split("-", 1)]
                        days = day_range(day_from, day_to)
                    elif group in DAYS_MAP:
                        days = [DAYS_MAP[group]]
                    else:
                        continue
                    for day in days:
                        oh.add_range(day, f"{int(start):02d}:00", f"{int(end):02d}:00")
        return oh
