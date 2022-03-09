# -*- coding: utf-8 -*-
import re

import scrapy
import json

from locations.items import GeojsonPointItem

class WoolworthsSpider(scrapy.Spider):
    #download_delay = 0.3
    name = "woolworths"
    item_attributes = {'brand': "Woolworths Supermarket"}
    allowed_domains = ["woolworths.com.au"]
    start_urls = ([
        'https://www.woolworths.com.au/shop/storelocator',
    ])
    def parse(self, response):
        with open('./locations/searchable_points/au_centroids_40km_radius.csv') as points:
            next(points)
            for point in points:
                row = point.replace('\n', '').split(',')
                lati = row[1]
                long = row[2]
                searchurl = 'https://www.woolworths.com.au/apis/ui/StoreLocator/Stores?Max=45&Division=SUPERMARKETS,PETROL,CALTEXWOW,AMPOLMETRO,AMPOL&Facility=&latitude={la}&longitude={lo}'.format(la=lati, lo=long)
                yield scrapy.Request((searchurl), callback=self.parse_search)

    def parse_search(self, response):
        data = json.loads(json.dumps(response.json()))

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