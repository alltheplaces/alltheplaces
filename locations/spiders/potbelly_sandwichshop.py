# -*- coding: utf-8 -*-
import scrapy
import json
import re
import demjson

from locations.items import GeojsonPointItem


class PotbellySandwichSpider(scrapy.Spider):

    name = "potbelly_sandwich"
    allowed_domains = ["www.potbelly.com"]
    start_urls = (
        'https://www.potbelly.com/dist/main.js',
    )

    def parse(self, response):
        results = removeNonAscii(response.body_as_unicode())
        sub_str = find_between(results, 'staticLocations=', "shown:!0}}]}")
        js_obj = sub_str + "shown:!0}}]"
        js_obj = js_obj.replace('!0', 'true')
        js_obj = js_obj.replace('!1', 'false')
        py_obj = demjson.decode(js_obj)
        dumped_str = json.dumps(py_obj)
        locations = json.loads(dumped_str)
        
        for data in locations:
            properties = {
                'ref': data['location']['id'],
                'name': data['location']['name'],
                'lat': data['location']['latitude'],
                'lon': data['location']['longitude'],
                'addr_full': data['location']['street_address'],
                'city': data['location']['locality'],
                'state': data['location']['region'],
                'postcode': data['location']['postal_code'],
                'phone': data['location']['phone'],
                'website': data['location']['facebook_url'],
                'opening_hours': data['location']['hours']
            }

            yield GeojsonPointItem(**properties)

def removeNonAscii(s): return "".join(i for i in s if ord(i)<128)

def find_between(s, first, last):
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start )
        return s[start:end]
    except ValueError:
        return ""