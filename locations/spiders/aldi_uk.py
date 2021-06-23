# -*- coding: utf-8 -*-
import json
import csv

import scrapy

from locations.items import GeojsonPointItem


class AldiUkSpider(scrapy.Spider):
    name = "aldiuk"
    item_attributes = {'brand': "Aldi"}
    allowed_domains = ['aldi.co.uk']


    def start_requests(self):
        url = "https://www.aldi.co.uk/api/store-finder/search?latitude={lat}&longitude={lng}"
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'}
        with open('./locations/searchable_points/eu_centroids_20km_radius_country.csv') as points:
            reader = csv.DictReader(points)
            for point in reader:
                if point["country"] == "UK":
                    yield scrapy.Request(
                        url=url.format(lat=point["latitude"], lng=point["longitude"]),
                        headers=headers,
                        callback=self.parse)

    def parse(self, response):
        data = json.loads(response.body_as_unicode())
        stores = data['results']
        for store in stores:
            properties = {
                'ref': store['code'],
                'name': store['name'],
                'addr_full': store['name'].strip('ALDI - '),
                'city': store['address'][0],
                'postcode': store['address'][1],
                'lat': store['latlng']['lat'],
                'lon': store['latlng']['lng'],
                'website': response.url
            }

            yield GeojsonPointItem(**properties)