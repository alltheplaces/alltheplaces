import json

import scrapy

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class Tele2SESpider(scrapy.Spider):
    name = "tele2_se"
    start_urls = ["https://www.tele2.se/butiker"]

    item_attributes = {"brand": "Tele2", "brand_wikidata": "Q309865"}

    def parse(self, response, **kwargs):
        stores_json = json.loads(
            response.xpath("//script[contains(text(), '__INITIAL_DATA__')]/text()")
            .get()
            .lstrip("window.__INITIAL_DATA__ = ")
        )
        for store in stores_json.get("state").get("entities").get("store").get("values").values():
            opening_hours = OpeningHours()
            website = store.get("slug")
            for day_index in range(7):
                if day_index <= 4:
                    open, close = store.get("weekdayOpenTimes").split("-")
                elif day_index == 5:
                    open, close = store.get("saturdayOpenTimes").split("-")
                else:
                    open, close = store.get("sundayOpenTimes").split("-")
                opening_hours.add_range(day=DAYS[day_index], open_time=open, close_time=close, time_format="%H")
            yield Feature(
                {
                    "ref": store.get("sys").get("id"),
                    "name": store.get("name"),
                    "street_address": store.get("address"),
                    "phone": store.get("phoneNumber"),
                    "postcode": store.get("zipCode"),
                    "city": store.get("city"),
                    "website": f"https://www.tele2.se/butiker/{website}" if website else None,
                    "lat": store.get("latitude"),
                    "lon": store.get("longitude"),
                    "opening_hours": opening_hours,
                }
            )
