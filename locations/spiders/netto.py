# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = {
    "Mo.": "Mo",
    "Di.": "Tu",
    "Mi.": "We",
    "Do.": "Th",
    "Fr.": "Fr",
    "Sa.": "Sa",
    "So.": "Su",
}


class NettoSpider(scrapy.Spider):
    name = "netto"
    item_attributes = {"brand": "Netto Marken-Discount", "brand_wikidata": "Q879858"}
    allowed_domains = ["netto-online.de"]

    def start_requests(self):
        url = "https://www.netto-online.de/INTERSHOP/web/WFS/Plus-NettoDE-Site/de_DE/-/EUR/ViewNettoStoreFinder-GetStoreItems"
        yield scrapy.http.FormRequest(
            url=url,
            method="POST",
            formdata={"n": "56.0", "e": "15.0", "w": "5.0", "s": "47.0"},
            callback=self.parse,
        )

    def parse_opening_hours(self, hours):
        DAYS = [
            "Mo.",
            "Di.",
            "Mi.",
            "Do.",
            "Fr.",
            "Sa.",
            "So.",
        ]

        opening_hours = OpeningHours()
        for block in hours.split("<br />"):
            if not block:
                continue
            days, hrs = block.split(":")
            if hrs.strip().lower() == "geschlossen":
                continue
            if "-" in days:
                start_day, end_day = days.split("-")
            else:
                start_day, end_day = days, days
            for day in DAYS[DAYS.index(start_day) : DAYS.index(end_day) + 1]:
                open_time, close_time = hrs.split("-")
                close_time = close_time.replace("Uhr", "").strip()
                open_time = open_time.strip()
                if open_time == "24.00":
                    open_time = "23.59"
                if close_time == "24.00":
                    close_time = "23.59"
                opening_hours.add_range(
                    day=DAY_MAPPING[day],
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H.%M",
                )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        stores = response.json()

        for store in stores:
            properties = {
                "ref": store["store_id"],
                "name": store["store_name"],
                "addr_full": store["street"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["post_code"],
                "country": "DE",
                "lat": store["coord_latitude"],
                "lon": store["coord_longitude"],
            }

            properties["opening_hours"] = self.parse_opening_hours(
                store["store_opening"]
            )

            yield GeojsonPointItem(**properties)
