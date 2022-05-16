# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class HibbettSportsSpider(scrapy.Spider):
    name = "hibbett_sports"
    item_attributes = {"brand": "Hibbett Sports", "brand_wikidata": "Hibbett Sports"}
    allowed_domains = ["hibbett.com"]
    start_urls = [
        "https://www.hibbett.com/on/demandware.store/Sites-Hibbett-US-Site/default/Stores-GetNearestStores?latitude=30.2175453&longitude=-97.8558357&countryCode=US&distanceUnit=mi&maxdistance=5000",
    ]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            day = DAY_MAPPING[hour[0]]

            open_hour, close_hour = hour[1].split(" - ")

            if len(open_hour) == 3:
                h = open_hour[:1]
                m = open_hour[-2:]
                open_hour = h + ":00" + m
            if len(open_hour) == 4:
                h = open_hour[:2]
                m = open_hour[-2:]
                open_hour = h + ":00" + m
            if len(close_hour) == 3:
                h = close_hour[:1]
                m = close_hour[-2:]
                close_hour = h + ":00" + m
            if len(close_hour) == 4:
                h = close_hour[:2]
                m = close_hour[-2:]
                close_hour = h + ":00" + m
            opening_hours.add_range(
                day=day,
                open_time=open_hour,
                close_time=close_hour,
                time_format="%H:%M%p",
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = response.json()

        nums = []
        for store in data["stores"]:
            nums.append(store)
        for num in nums:
            properties = {
                "ref": data["stores"][num]["id"],
                "name": data["stores"][num]["name"],
                "addr_full": data["stores"][num]["address1"],
                "city": data["stores"][num]["city"],
                "state": data["stores"][num]["stateCode"],
                "postcode": data["stores"][num]["postalCode"],
                "country": data["stores"][num]["countryCode"],
                "lat": data["stores"][num]["latitude"],
                "lon": data["stores"][num]["longitude"],
                "phone": data["stores"][num]["phone"],
            }

            try:
                hours = self.parse_hours(data["stores"][num]["storeHoursFormatted"])
                if hours:
                    properties["opening_hours"] = hours
            except:
                pass

            yield GeojsonPointItem(**properties)
