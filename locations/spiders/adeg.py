# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class AdegSpider(scrapy.Spider):
    name = "adeg"
    item_attributes = {"brand": "ADEG Österreich", "brand_wikidata": "Q290211"}
    allowed_domains = ["adeg.at"]
    start_urls = [
        "https://www.adeg.at/stores/data/",
    ]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for item in hours:
            opening_hours.add_range(
                day=item["dayOfWeek"][:2],
                open_time=item["opens"],
                close_time=item["closes"],
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        stores = response.json()

        for store in stores:
            properties = {
                "name": store["displayName"],
                "ref": store["storeId"],
                "addr_full": store["street"],
                "city": store["city"],
                "state": store["province"]["provinceName"],
                "postcode": store["zip"],
                "country": "AT",
                "phone": (store["telephoneAreaCode"] or "")
                + " "
                + (store["telephoneNumber"] or ""),
                "website": store.get("url") or None,
                "lat": float(store["yCoordinates"]),
                "lon": float(store["xCoordinates"]),
            }

            hours = self.parse_hours(store["openingTimesStructured"])
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
