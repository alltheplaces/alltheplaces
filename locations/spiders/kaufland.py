# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class KauflandSpider(scrapy.Spider):
    name = "kaufland"
    item_attributes = {"brand": "Kaufland", "brand_wikidata": "Q685967"}
    allowed_domains = ["kaufland.de"]
    start_urls = [
        "https://filiale.kaufland.de/.klstorefinder.json",
    ]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for hour in hours:
            day, open_time, close_time = hour.split("|")
            opening_hours.add_range(
                day=day[:2], open_time=open_time, close_time=close_time
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        stores = response.json()

        for store in stores:
            properties = {
                "name": store["cn"],
                "ref": store["n"],
                "addr_full": store["sn"],
                "city": store["t"],
                "postcode": store["pc"],
                "country": "DE",
                "phone": store["p"],
                "website": "https://www.kaufland.de/service/filiale.storeName={}.html".format(
                    store["n"]
                ),
                "lat": float(store["lat"]),
                "lon": float(store["lng"]),
            }

            hours = self.parse_hours(store["wod"])
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
