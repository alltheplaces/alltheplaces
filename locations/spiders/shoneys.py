import json
import re
import scrapy
from locations.items import GeojsonPointItem

keymap = {
    'addr_full': 'a',
    'city': 'c',
    'state': 's',
    'postcode': 'z',
    'name': 't',
    'lat': 'lt',
    'lon': 'ln',
}

class ShoneysSpider(scrapy.Spider):
    name = "shoneys"
    brand = "Shoney's"
    allowed_domains = ["static.batchgeo.com"]
    start_urls = (
        'https://static.batchgeo.com/map/json/b317db15b42986919f24bff19465e039/1482130242',
    )

    def parse(self, response):
        body = response.body_as_unicode()[6:-1]
        data = json.loads(body)
        stores = data['mapRS']                            
        properties = {}
        for store in stores:                                 
            for key1, key2 in keymap.items():
                if key2 in store and store[key2]:
                    properties[key1] = store[key2]

            properties['ref'] = properties['addr_full']
                
            yield GeojsonPointItem(**properties)             
