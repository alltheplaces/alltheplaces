# -*- coding: utf-8 -*-
import csv

import scrapy

from locations.items import GeojsonPointItem


class McDonaldsNLSpider(scrapy.Spider):
    name = "mcdonalds_nl"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["mcdonalds.nl"]
    download_delay = 2

    def start_requests(self):
        url = "https://www.mcdonalds.com/googleapps/GoogleRestaurantLocAction.do?method=searchLocation&latitude={lat}&longitude={lng}&radius=20&maxResults=100&country=nl&language=nl-nl"
        with open(
            "./locations/searchable_points/eu_centroids_20km_radius_country.csv"
        ) as points:
            reader = csv.DictReader(points)
            for point in reader:
                if point["country"] == "NL":
                    yield scrapy.Request(
                        url=url.format(lat=point["latitude"], lng=point["longitude"]),
                        callback=self.parse,
                    )

    def parse(self, response):
        data = response.json()
        for store in data["features"]:
            properties = {
                "ref": store["properties"]["id"],
                "name": store["properties"]["name"],
                "addr_full": store["properties"]["addressLine1"],
                "city": store["properties"]["addressLine3"],
                "postcode": store["properties"]["postcode"],
                "country": "NL",
                "phone": store.get("telephone"),
                "lat": float(store["geometry"]["coordinates"][1]),
                "lon": float(store["geometry"]["coordinates"][0]),
            }

            yield GeojsonPointItem(**properties)
