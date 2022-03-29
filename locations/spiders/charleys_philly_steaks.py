# -*- coding: utf-8 -*-
import re

import scrapy
import csv

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = {
    "Mon": "Mo",
    "Tue": "Tu",
    "Wed": "We",
    "Thu": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
    "Sun": "Su",
}


class CharleysPhillySteaksSpider(scrapy.Spider):
    name = "charleys_philly_steaks"
    allowed_domains = ["charleys.com"]
    start_urls = [
        "https://charleys.com/storelocator/StoreList/StoreList.ashx",
    ]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        hours_list = hours.split("<br />")

        if len(hours_list) != 1:
            for days in hours_list:
                if days != "":
                    day, h = days.split(": ")
                    day = DAY_MAPPING[day]
                    if h != "Closed":
                        open_time, close_time = h.split(" - ")
                        if close_time == "0:00AM":
                            close_time = "12:00AM"
                            opening_hours.add_range(
                                day=day,
                                open_time=open_time,
                                close_time=close_time,
                                time_format="%I:%M%p",
                            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        for row in csv.DictReader(response.text.splitlines()):
            properties = {
                "ref": row["store_id"],
                "name": row["store_name"],
                "addr_full": row["address1"],
                "city": row["city"],
                "state": row["state"],
                "postcode": row["zip"],
                "lat": row["lat"],
                "lon": row["lng"],
                "phone": row["phone1"],
            }

            hours = self.parse_hours(row["hours"])
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
