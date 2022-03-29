# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class MerkurSpider(scrapy.Spider):
    name = "merkur"
    item_attributes = {"brand": "Merkur", "brand_wikidata": "Q1921857"}
    allowed_domains = ["merkurmarkt.at"]
    start_urls = [
        "https://www.merkurmarkt.at/maerkte",
    ]

    def parse(self, response):
        yield scrapy.Request(
            "https://www.merkurmarkt.at/api/stores",
            headers={
                "Accept": "application/json",
                "correlationid": "af939ee6-26a9-4af4-bf8c-34a9bfc29b2b",
            },
            callback=self.parse_stores,
        )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for item in hours:
            try:
                open_time, close_time = item["time"].split(" - ")
            except KeyError:
                continue
            opening_hours.add_range(
                day=item["dayOfWeek"][:2], open_time=open_time, close_time=close_time
            )

        return opening_hours.as_opening_hours()

    def parse_stores(self, response):
        stores = response.json()

        for store in stores:
            properties = {
                "name": store["displayName"],
                "ref": store["storeId"],
                "addr_full": store["street"],
                "city": store["city"],
                "state": store["province"],
                "postcode": store["zip"],
                "country": "AT",
                "phone": store["phone"],
                "lat": float(store["coordinate"]["y"]),
                "lon": float(store["coordinate"]["x"]),
            }

            hours = self.parse_hours(store["openingTimes"])
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
