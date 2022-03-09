# -*- coding: utf-8 -*-
import re

import scrapy
import json

from locations.items import GeojsonPointItem

class WoolworthsSpider(scrapy.Spider):
    name = "woolworths"
    item_attributes = {'brand': "Woolworths Supermarket"}
    allowed_domains = ["woolworths.com.au"]
    start_urls = [
        'https://www.woolworths.com.au/shop/storelocator',
    ]

    def parse(self, response):
        with open('./locations/searchable_points/au_centroids_40km_radius.csv') as points:
            next(points)
            for point in points:
                row = point.replace('\n', '').split(',')
                lat = row[1]
                lon = row[2]
                search_url = f'https://www.woolworths.com.au/apis/ui/StoreLocator/Stores?Max=45&Division=SUPERMARKETS,PETROL,CALTEXWOW,AMPOLMETRO,AMPOL&Facility=&latitude={lat}&longitude={lon}'
                yield scrapy.Request(search_url, callback=self.parse_search)

    def parse_search(self, response):
        data = response.json()

        for i in data['Stores']:
            properties = {
                'ref': i['StoreNo'],
                'name': i['Name'],
                'addr_full': i['AddressLine1'],
                'city': i['Suburb'],
                'state': i['State'],
                'postcode': i['Postcode'],
                'country': "AU",
                'phone': i['Phone'],
                'lat': i['Latitude'],
                'lon': i['Longitude'],
            }

            yield GeojsonPointItem(**properties)
