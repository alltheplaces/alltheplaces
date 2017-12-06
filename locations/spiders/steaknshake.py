# -*- coding: utf-8 -*-
import scrapy
import json
import re


from locations.items import GeojsonPointItem


class SteaknshakeSpider(scrapy.Spider):
    name = "steaknshake"
    allowed_domains = ["www.steaknshake.com"]
    start_urls = (
        'https://www.steaknshake.com/zsapi/locations/',
    )


    def parse(self, response):
        results = json.loads(response.body_as_unicode())

        for data in results:

            properties = {
                'addr_full': "{} {} {} {} ".format(
                    data['address']['address1'],
                    data['address']['city'],
                    data['address']['region'],
                    data['address']['zip']
                                                  ),
                'city': data['address']['city'],
                'state': data['address']['region'],
                'postcode': data['address']['zip'],
                'ref': data['brandChainId'],
            }

            # Some items are not available for every location
            if 'loc' in data['address']:
                properties['lon'] = float(data['address']['loc'][0])
                properties['lat'] = float(data['address']['loc'][1])
            if data['hours']['sets']:
                properties['opening_hours'] = data['hours']['sets'][0]['hours']
            properties['phone'] = data.get('phone1')

            yield GeojsonPointItem(**properties)