# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = {0: "Su", 1: "Mo", 2: "Tu", 3: "We", 4: "Th", 5: "Fr", 6: "Sa"}


class KFCCanadaSpider(scrapy.Spider):
    name = "kfc_ca"
    item_attributes = {"brand": "KFC"}
    allowed_domains = ["kfc.ca"]
    start_urls = [
        "https://www.kfc.ca/find-a-kfc",
    ]

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()

        for store_day in store_hours:
            day = DAY_MAPPING[store_day.get("Day")]
            open_time = store_day.get("OpenTime")
            close_time = store_day.get("CloseTime")
            if open_time == "n/a" and close_time == "n/a":
                continue
            if open_time == "n/a" and close_time != "n/a":
                continue
            if open_time != "n/a" and close_time == "n/a":
                continue
            opening_hours.add_range(
                day=day,
                open_time=open_time,
                close_time=close_time,
                time_format="%I:%M %p",
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        store_details = response.xpath(
            '//script[contains(text(), "allRestDetails")]/text()'
        ).extract_first()
        data = json.loads(
            re.search(r"var allRestDetails = \'(.*)\';", store_details).group(1)
        )
        for store in data:

            properties = {
                "name": store["RestaurantName"],
                "ref": store["RestaurantId"],
                "addr_full": store["AddressLine1"],
                "city": store["City"],
                "state": store["Province"],
                "postcode": store["PostalCode"],
                "phone": store.get("PhoneNo"),
                "website": response.url,
                "lat": store.get("Lat"),
                "lon": store.get("Long"),
            }

            hours = self.parse_hours(store.get("Hours", []))
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
