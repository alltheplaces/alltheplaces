# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class PotbellySandwichSpider(scrapy.Spider):

    name = "potbelly_sandwich"
    allowed_domains = ["www.potbelly.com"]
    start_urls = (
        'https://www.potbelly.com/dist/main.js',
    )

    def parse(self, response):
        results = response.body_as_unicode()
        sub_str = find_between(results, 'staticLocations=', "shown:!0}}]}")
        js_obj = sub_str + "shown:!0}}]"
        js_obj = js_obj.replace('!0', 'true')
        js_obj = js_obj.replace('!1', 'false')
        js_obj = js_obj.replace(',hours:', ',"hours":')
        js_obj = js_obj.replace('\\r\\n', '; ')
        js_obj = re.sub(r'(-?[a-zA-Z]+):(\d{1,2}:)', r'\1: \2', js_obj)
        cleaner_js = re.sub(r'([a-z_]+):([^/ ])', r'"\1":\2', js_obj)
        locations = json.loads(cleaner_js)

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


def find_between(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""
