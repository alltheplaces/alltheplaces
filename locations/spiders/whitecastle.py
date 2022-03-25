# -*- coding: utf-8 -*-
import scrapy
import csv
import json
import re

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class WhiteCastleSpider(scrapy.Spider):
    name = "whitecastle"
    item_attributes = {"brand": "White Castle", "brand_wikidata": "Q1244034"}
    allowed_domains = ["www.whitecastle.com"]
    timeregex = re.compile("^([0-9:]+)(AM|PM)$")

    def start_requests(self):
        with open(
            "./locations/searchable_points/us_centroids_100mile_radius.csv"
        ) as points:
            for row in csv.DictReader(points):
                latitude = row["latitude"]
                longitude = row["longitude"]
                url = f"https://www.whitecastle.com/wcapi/location-search?lat={latitude}&lng={longitude}&dist=100"
                yield scrapy.Request(url, headers={"Accept": "application/json"})

    def store_hours(self, days):
        o = OpeningHours()

        for day in days:
            day_name = day.get("day")
            if not day_name:
                continue

            if day.get("closed"):
                continue

            if day.get("open24Hours"):
                o.add_range(day_name[:2], "00:00", "23:59")
                continue

            open_time, close_time = day.get("hours").split(" - ", 2)

            if close_time in ("12:00 AM", "Midnight"):
                close_time = "00:00 AM"

            o.add_range(day_name[:2], open_time, close_time, time_format="%H:%M %p")

        return o.as_opening_hours()

    def parse(self, response):
        data = json.loads(response.text)

        for store in data:
            properties = {
                "ref": store.get("storeNumber"),
                "name": store.get("name"),
                "addr_full": store.get("address"),
                "city": store.get("city"),
                "state": store.get("state"),
                "postcode": store.get("zip"),
                "phone": store.get("telephone"),
                "website": f'https://www.whitecastle.com/locations/{store.get("storeNumber")}',
                "lat": store.get("lat"),
                "lon": store.get("lng"),
            }

            if store.get("open24x7"):
                properties["opening_hours"] = "24/7"
            elif store.get("days"):
                opening_hours = self.store_hours(store.get("days"))
                if opening_hours:
                    properties["opening_hours"] = opening_hours

            yield GeojsonPointItem(**properties)
