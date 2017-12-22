# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import json

class SupervaluSpider(scrapy.Spider):
    name = "supervalu"
    allowed_domains = ["www.supervalustores.com"]
    
    def start_requests(self):
        url = 'http://www.supervalustores.com/tools/cm?getAll=cities'
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        stores = json.loads(response.body_as_unicode())
        for store in stores:
            properties = dict(
                city = store['city'],
                ref = store['id'],
                lat = store['lat'],
                lon = store['lng'],
                name = store['name'],
                phone = store['phone'],
                postcode = store['zip'],
                state = store['state'],
                addr_full = store['street']
                )
            yield GeojsonPointItem(**properties)

        
