# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem
from urllib.parse import urlencode

URL = "https://tdr.aaa.com/tdrl/search.jsp?"


class AAASpider(scrapy.Spider):
    name = "aaa"
    item_attributes = {
        "brand": "American Automobile Association",
        "brand_wikidata": "Q463436",
    }
    allowed_domains = ["tdr.aaa.com"]
    download_delay = 1.0

    def start_requests(self):
        point_files = [
            "./locations/searchable_points/us_centroids_50mile_radius.csv",
            "./locations/searchable_points/ca_centroids_50mile_radius.csv",
        ]

        for point_file in point_files:
            with open(point_file) as points:
                next(points)  # Ignore the header
                for point in points:
                    _, lat, lon = point.strip().split(",")

                    params = {
                        "searchtype": "O",
                        "radius": "5000",
                        "format": "json",
                        "ident": "AAACOM",
                        "destination": ",".join([lat, lon]),
                    }

                    yield scrapy.http.Request(
                        URL + urlencode(params), callback=self.parse
                    )

    def parse(self, response):
        location_data = json.loads(response.text)
        locations = location_data["aaa"]["services"].get("travelItems")

        # Handle inconsistent json objects
        if locations and isinstance(locations["travelItem"], list):
            for location in locations["travelItem"]:
                properties = {
                    "ref": location["id"],
                    "name": location["itemName"],
                    "addr_full": location["addresses"]["address"]["addressLine"],
                    "city": location["addresses"]["address"]["cityName"],
                    "state": location["addresses"]["address"]["stateProv"]["code"],
                    "postcode": location["addresses"]["address"]["postalCode"],
                    "country": location["addresses"]["address"]["countryName"]["code"],
                    "lat": location["position"]["latitude"],
                    "lon": location["position"]["longitude"],
                    "phone": location["phones"].get("phone", {}).get("content"),
                }

                yield GeojsonPointItem(**properties)
        elif (
            locations
        ):  # if there is data and the response has one location not structured in a list
            location = locations["travelItem"]
            properties = {
                "ref": location["id"],
                "name": location["itemName"],
                "addr_full": location["addresses"]["address"]["addressLine"],
                "city": location["addresses"]["address"]["cityName"],
                "state": location["addresses"]["address"]["stateProv"]["code"],
                "postcode": location["addresses"]["address"]["postalCode"],
                "country": location["addresses"]["address"]["countryName"]["code"],
                "lat": location["position"]["latitude"],
                "lon": location["position"]["longitude"],
                "phone": location["phones"].get("phone", {}).get("content"),
            }

            yield GeojsonPointItem(**properties)
