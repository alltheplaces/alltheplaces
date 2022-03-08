# -*- coding: utf-8 -*-
import re

import scrapy
import json

from locations.items import GeojsonPointItem

class GoodstartsSpider(scrapy.Spider):
    #download_delay = 0.3
    name = "goodstart"
    item_attributes = {'brand': "GoodStart Early Learning"}
    allowed_domains = ["goodstart.org.au"]
    start_urls = ([
        'https://www.goodstart.org.au/extApi/CentreAPI/',
    ])
    def parse(self, response):
        data = json.loads(json.dumps(response.json()))
        for i in data['centres']:
            properties = {
                'ref': i['NodeAliasPath'],
                'name': i['Name'],
                'addr_full': i['Address'],
                'country': "AU",
                'phone': i['Phone'],
                'lat': i['Latitude'],
                'lon': i['Longitude'],
            }

            yield GeojsonPointItem(**properties)
