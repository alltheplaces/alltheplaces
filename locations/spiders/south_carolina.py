# -*- coding: utf-8 -*-
import re

import scrapy
import json

from locations.items import GeojsonPointItem

class SCSpider(scrapy.Spider):
    download_delay = 0.2
    name = "south_carolina"
    item_attributes = {'brand': "State of South Carolina", 'brand_wikidata': "Q53709977"}
    allowed_domains = ["sc.gov"]
    start_urls = (
        'https://applications.sc.gov/PortalMapApi/api/Map/GetMapItemsByCategoryId/1,2,3,4,5,6,7',
    )

    def parse(self, response):
        cat = ('State Park', 'Library', 'Department of Health and Human Resources',
               'Court House', 'Department of Mental Health', 'Department of Motor Vehicles', 'SC Works')

        data = json.loads(json.dumps(response.json()))
        # ziptext = zipre[0]
        # ziptext = ziptext.replace(',SC', ', SC')
        # for item in replace_list:
        #     ziptext = ziptext.replace(item, '')
        #
        # ziptext2 = ziptext.split('{')
        print(data[0])

        for i in data:
            print (i['Address'])

            properties = {
                'ref': i['Id'],
                'name': i['Description'],
                'extras': (cat[int(i['CategoryId']) - 1]),
                'addr_full': i['Address'],
                'city': '',
                'state': '',
                'postcode': i['Zipcode'],
                'country': 'US',
                'phone': i['Telephone'],
                'lat': float(i['Latitude']),
                'lon': -abs(float(i['Longitude'])),
            }

            yield GeojsonPointItem(**properties)
