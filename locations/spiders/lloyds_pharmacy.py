# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

URL = "https://store-locator.mohc.net/store-locator"
DAY_MAPPING = {
    "mon": "Mo",
    "tue": "Tu",
    "wed": "We",
    "thu": "Th",
    "fri": "Fr",
    "sat": "Sa",
    "sun": "Su",
}


class LloydsPharmacySpider(scrapy.Spider):
    name = "lloyds_pharmacy"
    allowed_domains = ["mohc.net"]
    item_attributes = {"brand": "LloydsPharmacy", "brand_wikidata": "Q6662870"}

    def start_requests(self):
        yield scrapy.http.Request(url=URL, callback=self.parse, method="GET")

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for day in DAY_MAPPING:
            weekday = DAY_MAPPING[day]
            weekday_hours = hours[day]
            if weekday_hours:
                open_time = weekday_hours[0]
                close_time = weekday_hours[1]
                opening_hours.add_range(
                    day=weekday,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M",
                )
            else:
                continue

        return opening_hours.as_opening_hours()

    def parse(self, response):
        store_data = json.loads(response.text)
        stores = store_data.get("stores")

        for store in stores:
            address = store["address"]
            town = address["town"]
            locality = address["locality"]

            if locality and locality != town:
                if town:
                    city = town
                    addr = " ".join([address["street"], locality])
                else:
                    city = locality
                    addr = address["street"]
            else:
                city = town
                addr = address["street"]

            coords = store["location"]
            lat = coords.get("lat")
            lon = coords.get("lng")
            if lat == 0:
                lat, lon = None, None

            properties = {
                "ref": store["id"],
                "name": store["name"],
                "addr_full": addr,
                "city": city,
                "postcode": address["postcode"],
                "country": "GB",
                "lat": lat,
                "lon": lon,
                "phone": store["phone"],
            }

            hours = store.get("hours")
            if hours:
                properties["opening_hours"] = self.parse_hours(hours)

            yield GeojsonPointItem(**properties)
