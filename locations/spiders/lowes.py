# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import json 

states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", 
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
"SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"] # U.S States

provinces = ['ON', 'QC', 'NS', 'NB', 'MB', 'BC', 'PE', 'SK', 'AB', 'NL'] # Canadian Provinces

headers = {"Referer": "http://lowes.know-where.com/lowes/cgi/region_list", 
           'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64…) Gecko/20100101 Firefox/57.0'}

class LowesSpider(scrapy.Spider):
    """" This spider scrapes Lowes store locations """
    name = 'lowes'
    allowed_domains = ['https://know-where.com']
    start_url = 'http://lowes.know-where.com/lowes/cgi/region_list'
    
    def start_requests(self):
        us_url = 'http://lowes.know-where.com/lowes/cgi/region?all=true&country=US&region={}&design=default&lang=en&option=&mapid=NorthAmerica'
        canada_url = 'http://lowes.know-where.com/lowes/cgi/region?country=CA&region={}&design=default&lang=en&option=&mapid=NorthAmerica'

        for state in states:
            state_url = us_url.format(state)
            request = scrapy.Request(state_url, callback=self.parse, headers=headers)
            request.meta['state'] = state
            yield request
            
        for province in provinces:
            province_url = canada_url.format(province)
            request = scrapy.Request(province_url, callback=self.parse)
            request.meta['state'] = province 
            yield request
            
    def parse(self, response):
        for store in response.xpath('//div[@class = \"address-block\"]'):
            store_data = store.css('li::text').extract()
            store_number = store.css('li::text').extract_first()
            city_state_zip = store_data[2]
            comma_index = city_state_zip.find(',') # A comma is at the end of the city name
            city = city_state_zip[:comma_index]    # Gets the city name

            result = GeojsonPointItem(
                ref = store_number, 
                state = response.meta['state'],
                addr_full = store_data[1],
                city = city)

            yield result 
