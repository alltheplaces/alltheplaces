# -*- coding: utf-8 -*-
import scrapy
import ast
from uszipcode import ZipcodeSearchEngine
from locations.items import GeojsonPointItem

STATES = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA',
          'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
          'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
          'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
          'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

class MeijerSpider(scrapy.Spider):
    name = 'meijer'
    allowed_domains = ['www.meijer.com']

    def start_requests(self):
        search = ZipcodeSearchEngine()
        for state in STATES:
            location = search.by_state(state)
            if state == 'MI':
                yield scrapy.Request(
                    'https://www.meijer.com/custserv/locate_store_layer.cmd?latitude={}&longitude={}&radius=50&editLinktype=&fromGeolocation=true'.format(location[0]['Latitude'], location[0]['Longitude']),
                    callback = self.parse
                )
    
    def parse(self, response):
        selector = scrapy.Selector(response)
        stores = selector.css('div.records_inner>script::text').extract_first().strip()[13:-1]
        for store in ast.literal_eval(stores):
            address1 = store[6].split(',')
            city = address1[0].strip()
            address2 = address1[1].strip().split(' ')
            state = address2[0]
            postcode = address2[1]
            properties = {
                'ref': store[0],
                'name': store[1],
                'phone': store[7],
                'opening_hours': self.hours(store[8]),
                'lat': store[37],
                'lon': store[36],
                'street': store[2],
                'city': city,
                'state': state,
                'postcode': postcode
            }
            
            yield GeojsonPointItem(**properties)

    def hours(self, data):
        if data == 'Open 24 hrs a day, 364 days a year.':
            return '24/7'
        else :
            return data

        
        
