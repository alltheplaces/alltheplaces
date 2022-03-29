# -*- coding: utf-8 -*-
import csv

import scrapy

from locations.items import GeojsonPointItem

COUNTRY = {"1": "DE", "5": "AT", "6": "CZ", "8": "PL", "9": "NL"}


class KikSpider(scrapy.Spider):
    name = "kik"
    item_attributes = {"brand": "Kik"}
    allowed_domains = ["kik.de"]

    def start_requests(self):
        url = "https://www.kik.de/storefinder/results.json?searchlocation=Germany&lat={lat}&long={lng}&country=DE"
        with open(
            "./locations/searchable_points/eu_centroids_20km_radius_country.csv"
        ) as points:
            reader = csv.DictReader(points)
            for point in reader:
                if point["country"] == "DE":
                    yield scrapy.Request(
                        url=url.format(lat=point["latitude"], lng=point["longitude"]),
                        callback=self.parse,
                    )

    def parse(self, response):
        data = response.json()
        for store in data["stores"]:
            country = store["country"]
            properties = {
                "ref": store["filiale"],
                "addr_full": store["address"],
                "city": store["city"],
                "postcode": store["zip"],
                "country": COUNTRY[country],
                "lat": float(store["latitude"]),
                "lon": float(store["longitude"]),
            }

            yield GeojsonPointItem(**properties)
