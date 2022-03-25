# -*- coding: utf-8 -*-
import json
import re

import scrapy

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


class EarthFareSpider(scrapy.Spider):
    name = "earth_fare"
    item_attributes = {"brand": "Earth Fare"}
    allowed_domains = ["www.earthfare.com"]
    start_urls = [
        "https://www.earthfare.com/rs/StoreLocator",
    ]

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()

        days = list(DAY_MAPPING.keys())
        day_range, open_close = re.split(r", | ", store_hours)
        start_day, end_day = day_range.split("-")
        start_time, end_time = open_close.split("-")

        for day in days[days.index(start_day) : days.index(end_day) + 1]:
            opening_hours.add_range(
                day=DAY_MAPPING[day],
                open_time=start_time,
                close_time=end_time,
                time_format="%I%p",
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        stores = response.xpath(
            '//script[@type="text/javascript" and contains(text(), "storeDetail")]/text()'
        ).extract_first()
        store_data = re.findall(r"(\{\\\"Distance\\\".*?\"\})[,\]]", stores)

        for store in store_data:
            store_details = json.loads(store.replace("\\", ""))

            properties = {
                "name": store_details["StoreName"],
                "ref": store_details["CS_StoreID"],
                "addr_full": store_details["Address1"],
                "city": store_details["City"],
                "state": store_details["State"],
                "postcode": store_details["Zipcode"],
                "phone": store_details.get("PhoneNumber"),
                "website": "https://www.earthfare.com/rs/StoreLocator?id={0}".format(
                    store_details["CS_StoreID"]
                ),
                "lat": store_details.get("Latitude"),
                "lon": store_details.get("Longitude"),
            }

            hours = store_details.get("StoreHours")
            if hours:
                properties["opening_hours"] = self.parse_hours(hours)

            yield GeojsonPointItem(**properties)
