# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class AlbertAndWalterSpider(scrapy.Spider):

    name = "albert_walter"
    allowed_domains = ["www.aw.ca"]
    start_urls = (
        'https://web.aw.ca/api/locations/',
    )

    def parse(self, response):
        results = json.loads(response.body_as_unicode())
        for data in results:
            properties = {
                'ref': data['restnum'],
                'name': data['restaurant_name'],
                'lat': data['latitude'],
                'lon': data['longitude'],
                'addr_full': data['public_address'], # data['address1'] + ' ' + data['address2'],
                'city': data['city_name'],
                'state': data['province_code'],
                'postcode': data['postal_code'],
                'phone': data['phone_number'],
                'opening_hours': data['hours']            
                }

            yield GeojsonPointItem(**properties)
