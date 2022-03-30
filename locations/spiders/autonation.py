# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = {0: "Mo", 1: "Tu", 2: "We", 3: "Th", 4: "Fr", 5: "Sa", 6: "Su"}


class AutoNationSpider(scrapy.Spider):
    name = "auto_nation"
    allowed_domains = ["autonation.com"]
    start_urls = [
        "https://www.autonation.com/StoreDetails/Get/?lat=30.218908309936523&long=-97.8546142578125&radius=5000\
        &zipcode=78749&d=1602263009819",
    ]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for hour in hours:
            try:
                day = DAY_MAPPING[hour["Day"]]
                open_time = hour["StartTime"]
                if len(open_time) == 7:
                    open_time = open_time.rjust(8, "0")
                close_time = hour["EndTime"]
                if len(close_time) == 7:
                    close_time = close_time.rjust(8, "0")
                if open_time == "":
                    continue
            except:
                continue

            opening_hours.add_range(
                day=day,
                open_time=open_time,
                close_time=close_time,
                time_format="%I:%M %p",
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        stores = response.json()

        for store in stores["Store"]:
            properties = {
                "ref": store["StoreId"],
                "name": store["Name"],
                "addr_full": store["AddressLine1"],
                "city": store["City"],
                "state": store["StateCode"],
                "postcode": store["PostalCode"],
                "country": "US",
                "lat": store["Latitude"],
                "lon": store["Longitude"],
                "phone": store["Phone"],
                "brand": store["Makes"],
                "website": "https://www.autonation.com/dealers/"
                + store["StoreDetailsUrl"],
            }

            hours = self.parse_hours(store["StoreDetailedHours"])

            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
