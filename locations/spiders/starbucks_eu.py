# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class StarbucksEUSpider(scrapy.Spider):
    name = "starbucks_eu"
    allowed_domains = ["https://www.starbucks.co.uk/"]

    def start_requests(self):
        base_url = "https://www.starbucks.co.uk/api/v1/store-finder?latLng={lat}%2C{lon}"

        with open('./locations/searchable_points/eu_centroids_20km_radius_country.csv') as points:
            next(points)  # Ignore the header
            for point in points:
                _, lat, lon, country = point.strip().split(',')
                url = base_url.format(lat=lat, lon=lon)

                yield scrapy.http.Request(url=url, callback=self.parse)

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        for place in data["stores"]:
            try:
                addr, postal_city = place["address"].strip().split('\n')
            except:
                addr, addr_2, postal_city = place["address"].strip().split('\n')

            try:
                city_hold = re.search(
                    r'\s([A-Z]{1,2}[a-z]*)$|\s([A-Z]{1}[a-z]*)(\s|,\s)([A-Z]{1,2}[a-z]*)$|\s([A-Z]{1}[a-z]*)\s([0-9]*)$',
                    postal_city).groups()
                res = [i for i in city_hold if i]

                if ", " in res:
                    city = "".join(res)
                else:
                    city = " ".join(res)

                postal = postal_city.replace(city, "").strip()
            except:
                city = postal_city
                postal = postal_city

            properties = {
                'ref': place["id"],
                'name': place["name"],
                'addr_full': addr,
                'city': city,
                'postcode': postal,
                'lat': place["coordinates"]["lat"],
                'lon': place["coordinates"]["lng"],
                'phone': place["phoneNumber"]
            }

            yield GeojsonPointItem(**properties)
