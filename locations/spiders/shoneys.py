import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class ShoneysSpider(scrapy.Spider):
    name = "shoneys"
    item_attributes = {"brand": "Shoney's", "brand_wikidata": "Q7500392"}
    allowed_domains = ["shoneys.com"]
    start_urls = ("https://www.shoneys.com/wp-json/wp/v2/locations",)

    def parse(self, response):
        for row in response.json():
            hours = OpeningHours()
            for day, interval in row["acf"]["working_hours"].items():
                if interval in ("", "CLOSED"):
                    continue
                open_time, close_time = re.split(" ?- ?", interval.replace("to", "-"))
                hours.add_range(day[:2].capitalize(), open_time.strip(), close_time.strip(), "%I:%M%p")
            properties = {
                "ref": row["id"],
                "lat": row["acf"]["address"]["lat"],
                "lon": row["acf"]["address"]["lng"],
                "website": row["link"],
                "name": row["title"]["rendered"],
                "addr_full": row["acf"]["address"]["address"],
                "phone": row["acf"]["phone"],
                "opening_hours": hours.as_opening_hours(),
            }
            yield Feature(**properties)
