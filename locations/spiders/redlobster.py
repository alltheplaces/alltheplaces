# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class RedLobsterSpider(scrapy.Spider):
    name = "redlobster"
    allowed_domains = ["redlobster.com"]
    start_urls = (
        'https://www.redlobster.com/api/location/GetLocations?latitude=38.9072&longitude=-77.0369&radius=150000',
    )

    def parse(self, response):
        results = json.loads(response.body_as_unicode())
        for store_data in results["locations"]:
            for location in store_data['location']:
                properties = {
                    'addr_full': location['address1'],
                    'city': location['city'],
                    'state': location['state'],
                    'phone': location['phone'],
                    'website': location['localPageURL'],
                    'ref': location['rlid'],
                    'lon':float(location['longitude']),
                    'lat':float(location['latitude']),
                }

        yield GeojsonPointItem(**properties)