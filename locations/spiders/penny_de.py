# -*- coding: utf-8 -*-
import csv
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class PennyDESpider(scrapy.Spider):
    name = "penny_de"
    item_attributes = {'brand': 'Penny', 'brand_wikidata': 'Q284688'}
    allowed_domains = ["penny.de"]
    download_delay = 0.5

    def start_requests(self):
        url = "https://www.penny.de/marktsuche/?type=666&tx_pennyregionalization_googlemarket[location]={lat},{lng}"

        with open('./locations/searchable_points/eu_centroids_20km_radius_country.csv') as points:
            reader = csv.DictReader(points)
            for point in reader:
                if point["country"] == "DE":
                    yield scrapy.Request(
                        url=url.format(lat=point["latitude"], lng=point["longitude"]),
                        callback=self.parse
                    )

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        for store in data["markets"]:
            properties = {
                'name': store["name"],
                'ref': store["marketId"],
                'addr_full': store["address"],
                'city': store["city"],
                'postcode': store["zip"],
                'country': "DE",
                'lat': float(store["lat"]),
                'lon': float(store["lng"]),
            }

            yield GeojsonPointItem(**properties)
