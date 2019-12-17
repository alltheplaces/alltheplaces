# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem

STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", 
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
HEADERS = { 'Content-Type': 'application/json' }
JJBASE = 'https://www.jimmyjohns.com/webservices/Location/LocationServiceHandler.asmx/{}'
CITIES = JJBASE.format('GetCitiesByStateNameAbbreviation')
STORES = JJBASE.format('GetStoreAddressesByCityAndState')

class JimmyJohnsSpider(scrapy.Spider):
    name = "jimmy-johns"
    item_attributes = { 'brand': "Jimmy John's" }
    allowed_domains = ["www.jimmyjohns.com"]
    download_delay = 0.2

    def start_requests(self):
        for state in STATES:
            current_state = json.dumps({ 'state': state })
            request = scrapy.Request(
                CITIES, 
                method='POST',
                body=current_state,
                headers=HEADERS,
                callback=self.parse_cities
            )
            request.meta['state'] = state
            yield request
    
    def parse_cities(self, response):
        cities = json.loads(response.body)
        for city in cities['d']:
            current_city = json.dumps({ 'state': response.meta['state'], 'city': city })
            request = scrapy.Request(
                STORES,
                method='POST',
                body=current_city,
                headers=HEADERS,
                callback=self.parse
            )
            yield request

    def parse(self, response):
        stores = json.loads(response.body)
        for store in stores['d']:
            full = '{}, {}, {} {}'.format(store['address'], store['city'], store['state'], store['postalcode'])
            yield GeojsonPointItem(
                name=store['storename'],
                addr_full=full,
                opening_hours=store['hours'],
                phone=store['telephone'],
                ref=store['storeid'],
                lon=float(store['lng']),
                lat=float(store['lat']),
            )
