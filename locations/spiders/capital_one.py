# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = {
    "Sunday": "Su",
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
}
BASE_URL = "https://api.capitalone.com/locations"


class CapitalOneSpider(scrapy.Spider):
    name = "capital_one"
    item_attributes = {"brand": "Capital One", "brand_wikidata": "Q1034654"}
    allowed_domains = ["api.capitalone.com"]
    download_delay = 0.5

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for weekday in hours:
            day = DAY_MAPPING[weekday["day"]]
            open_time = weekday["open"]
            if open_time == "Closed":
                continue
            close_time = weekday["open"]
            opening_hours.add_range(
                day=day,
                open_time=open_time,
                close_time=close_time,
                time_format="%I:%M %p",
            )
        return opening_hours.as_opening_hours()

    def start_requests(self):
        with open(
            "./locations/searchable_points/us_centroids_50mile_radius.csv"
        ) as points:
            next(points)  # Ignore the header
            for point in points:
                row = point.split(",")
                lat = float(row[1])
                lon = float(row[2])

                raw = {
                    "variables": {
                        "input": {
                            "lat": lat,
                            "long": lon,
                            "radius": 50,
                            "locTypes": ["branch", "cafe"],
                            "servicesFilter": [],
                        }
                    },
                    "query": "\n        query geoSearch($input: GeoSearchInput\u0021){\n          geoSearch(input: $input){\n            locType\n            locationName\n            locationId\n            address {\n              addressLine1\n              stateCode\n              postalCode\n              city\n            }\n            services\n            distance\n            latitude\n            longitude\n            slug\n            seoType\n            ... on Atm {\n              open24Hours\n            }\n            ... on Branch {\n              phoneNumber\n              timezone\n              lobbyHours {\n                day\n                open\n                close\n              }\n              driveUpHours {\n                day\n                open\n                close\n              }\n              temporaryMessage\n              reopenDate\n            }\n            ... on Cafe {\n              phoneNumber\n              photo\n              timezone\n              hours {\n                day\n                open\n                close\n              }\n              temporaryMessage\n              reopenDate\n            }\n          }\n        }",
                }

                headers = {
                    "Accept": "application/json;v=1",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Connection": "keep-alive",
                    "Content-Type": "application/json",
                }

                yield scrapy.http.Request(
                    BASE_URL,
                    self.parse,
                    method="POST",
                    body=json.dumps(raw),
                    headers=headers,
                )

    def parse(self, response):
        data = json.loads(response.text)
        location_data = data["data"]["geoSearch"]

        if location_data:
            for location in location_data:
                properties = {
                    "ref": location["locationId"],
                    "name": location["locationName"],
                    "addr_full": location["address"]["addressLine1"],
                    "city": location["address"]["city"],
                    "state": location["address"]["stateCode"],
                    "postcode": location["address"]["postalCode"],
                    "lat": location["latitude"],
                    "lon": location["longitude"],
                    "phone": location["phoneNumber"],
                    "website": "/".join(
                        [
                            "https://locations.capitalone.com/bank",
                            location["address"]["stateCode"],
                            location["slug"],
                        ]
                    ),
                    "extras": {"location_type": location["locType"]},
                }

                hours = location.get("hours", location.get("lobbyHours", ""))
                if hours:
                    store_hours = self.parse_hours(hours)
                    properties["opening_hours"] = store_hours

                yield GeojsonPointItem(**properties)
