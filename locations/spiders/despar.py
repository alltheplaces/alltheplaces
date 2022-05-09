# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem

class DesparSpider(scrapy.Spider):
    #download_delay = 0.2
    name = "despar"
    item_attributes = {'brand': "Despar"}
    allowed_domains = ["despar.com"]

    start_urls = ([
        'https://www.despar.com'
    ])

    def parse(self, response):
        with open('./locations/searchable_points/eu_centroids_20km_radius_country.csv') as points:
            next(points)
            for point in points:
                row = point.replace('\n', '').split(',')
                lati = row[1]
                long = row[2]
                country = row[3]
                if country == "IT":
                    searchurl = 'https://www.despar.com/SearchPdvs?lat={la}&lng={lo}'.format(la=lati, lo=long)
                    yield scrapy.Request(response.urljoin(searchurl), callback=self.parse_search)

    def parse_search(self, response):
        data = response.json()
        for i in data:
            properties = {
                'ref': i['codice'],
                'name': i['nome'],
                'addr_full': i['indirizzo'],
                'city': i['citta'],
                'country': 'IT',
                'lat': float(i['lat']),
                'lon': float(i['lng']),
            }

            yield GeojsonPointItem(**properties)