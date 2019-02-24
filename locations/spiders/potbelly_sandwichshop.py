# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class PotbellySandwichSpider(scrapy.Spider):

    name = "potbelly_sandwich"
    allowed_domains = ["www.potbelly.com"]
    start_urls = (
        'https://api-potbelly-production.fuzzstaging.com/proxy/all-locations',
    )

    def parse(self, response):
        results = response.body_as_unicode()
        locations = json.loads(results)

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
