# -*- coding: utf-8 -*-
import re
import csv
import scrapy
import json

from locations.items import GeojsonPointItem


class SmashburgerSpider(scrapy.Spider):
    download_delay = 0.2
    name = "smashburger"
    item_attributes = {"brand": "Smashburger", "brand_wikidata": "Q17061332"}
    allowed_domains = ["smashburger.com"]

    def start_requests(self):
        with open(
            "./locations/searchable_points/us_centroids_100mile_radius.csv"
        ) as points:
            reader = csv.DictReader(points)
            for point in reader:
                url = f'https://api.smashburger.com/mobilem8-web-service/rest/storeinfo/distance?_=1649446017671&attributes=&disposition=PICKUP&latitude={point["latitude"]}&longitude={point["longitude"]}&maxResults=100&radius=100&radiusUnit=mi&statuses=ACTIVE,TEMP-INACTIVE&tenant=sb-us'
                yield scrapy.Request(url, callback=self.parse_search)

    def parse_search(self, response):
        data = response.json()
        for i in data["getStoresResult"]["stores"]:
            properties = {
                "ref": i["storeName"],
                "name": i["storeName"],
                "addr_full": i["street"],
                "city": i["city"],
                "state": i["state"],
                "postcode": i["zipCode"],
                "country": i["country"],
                "phone": i["phoneNumber"],
                "lat": float(i["latitude"]),
                "lon": float(i["longitude"]),
            }

            yield GeojsonPointItem(**properties)
