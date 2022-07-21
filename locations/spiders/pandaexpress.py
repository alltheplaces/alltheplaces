# -*- coding: utf-8 -*-
import csv

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class PandaExpressSpider(scrapy.Spider):
    name = "pandaexpress"
    item_attributes = {"brand": "Panda Express", "brand_wikidata": "Q1358690"}
    allowed_domains = ["pandaexpress.com"]
    # download_delay = 0.5
    def start_requests(self):
        with open(
            "./locations/searchable_points/us_centroids_10mile_radius.csv"
        ) as points:
            reader = csv.DictReader(points)
            for point in reader:
                params = {
                    "lat": point["latitude"],
                    "lng": point["longitude"],
                }

                url = f"https://nomnom-prod-api.pandaexpress.com/restaurants/near?lat={params.get('lat')}&long={params.get('lng')}&radius=100&limit=200&nomnom=calendars&nomnom_calendars_from=20220720&nomnom_calendars_to=20220731&nomnom_exclude_extref=99997,99996,99987,99988,99989,99994,11111,8888,99998,99999,0000"
                yield scrapy.Request(url, callback=self.parse_stores)
        with open(
            "./locations/searchable_points/ca_centroids_25mile_radius.csv"
        ) as points:
            reader = csv.DictReader(points)
            for point in reader:
                params = {
                    "lat": point["latitude"],
                    "lng": point["longitude"],
                }

                url = f"https://nomnom-prod-api.pandaexpress.com/restaurants/near?lat={params.get('lat')}&long={params.get('lng')}&radius=100&limit=200&nomnom=calendars&nomnom_calendars_from=20220720&nomnom_calendars_to=20220731&nomnom_exclude_extref=99997,99996,99987,99988,99989,99994,11111,8888,99998,99999,0000"
                yield scrapy.Request(url, callback=self.parse_stores)

    def parse_stores(self, response):
        data = response.json()

        for store in data["restaurants"]:
            oh = OpeningHours()
            if len(store.get("calendars").get("calendar")) > 0:
                calendar_ranges = (
                    store.get("calendars").get("calendar")[0].get("ranges")
                )
                for oh_range in calendar_ranges:
                    oh.add_range(
                        oh_range.get("weekday")[:2],
                        oh_range.get("start").split(" ")[-1],
                        oh_range.get("end").split(" ")[-1],
                        time_format="%H:%M",
                    )
            properties = {
                "ref": store["id"],
                "lat": store["latitude"],
                "lon": store["longitude"],
                "name": store["name"],
                "street_address": store["streetaddress"],
                "opening_hours": oh.as_opening_hours(),
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zip"],
                "country": store["country"],
                "phone": store["telephone"],
            }
            yield GeojsonPointItem(**properties)
