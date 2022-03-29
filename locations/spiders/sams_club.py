# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAYS = ["Mo", "Tu", "We", "Th", "Fr"]


class SamsClubSpider(scrapy.Spider):
    name = "sams_club"
    item_attributes = {"brand": "Sam's Club"}
    allowed_domains = ["www.samsclub.com"]
    start_urls = [
        "https://www.samsclub.com/api/node/clubfinder/list?distance=10000&nbrOfStores=600&singleLineAddr=78749",
    ]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        if "saturdayHrs" in hours:
            day = "Sa"
            open_time = hours["saturdayHrs"]["startHr"]
            close_time = hours["saturdayHrs"]["endHr"]
            opening_hours.add_range(
                day=day, open_time=open_time, close_time=close_time, time_format="%H:%M"
            )
        if "sundayHrs" in hours:
            day = "Su"
            open_time = hours["sundayHrs"]["startHr"]
            close_time = hours["sundayHrs"]["endHr"]
            opening_hours.add_range(
                day=day, open_time=open_time, close_time=close_time, time_format="%H:%M"
            )
        if "monToFriHrs" in hours:
            open_time = hours["monToFriHrs"]["startHr"]
            close_time = hours["monToFriHrs"]["endHr"]
            for day in DAYS:
                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = response.json()

        for store in data:
            properties = {
                "ref": store["id"],
                "name": store["name"],
                "addr_full": store["address"]["address1"],
                "city": store["address"]["city"],
                "state": store["address"]["state"],
                "postcode": store["address"]["postalCode"],
                "country": store["address"]["country"],
                "lat": store["geoPoint"]["latitude"],
                "lon": store["geoPoint"]["longitude"],
                "phone": store["phone"],
                "extras": {
                    "amenity:fuel": "gas" in store["services"],
                    "amenity:pharmacy": "pharmacy" in store["services"],
                    "fuel:propane": "propane_exchange" in store["services"],
                },
            }

            hours = self.parse_hours(store["operationalHours"])

            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
