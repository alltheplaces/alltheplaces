# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class VictraSpider(scrapy.Spider):
    name = "victra"
    item_attributes = {"brand": "Victra"}
    allowed_domains = []
    start_urls = [
        "https://victra.com/Handlers/LocationData.ashx",
    ]

    def parse_hours(self, store):
        opening_hours = OpeningHours()

        for hour in [
            "mon_hours",
            "tue_hours",
            "wed_hours",
            "thu_hours",
            "fri_hours",
            "sat_hours",
            "sun_hours",
        ]:
            hours = store[hour]
            if hours == "CLOSED":
                continue
            open_time, close_time = hours.split("-")
            opening_hours.add_range(
                day=hour[:2].capitalize(),
                open_time=open_time,
                close_time=close_time,
                time_format="%I:%M%p",
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        stores = response.json()

        for store in stores:
            properties = {
                "name": store["name"],
                "ref": store["id"],
                "addr_full": store["address"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["postal"],
                "phone": store.get("phone"),
                "lat": float(store["lat"]),
                "lon": float(store["lng"]),
            }

            hours = self.parse_hours(store)
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
