# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class RedLobsterSpider(scrapy.Spider):
    name = "redlobster5"
    allowed_domains = ["redlobster.com"]
    start_urls = (
        'https://www.redlobster.com/api/location/GetLocations?latitude=38.9072&longitude=-77.0369&radius=150000',
    )

    def parse(self, response):
        results = json.loads(response.body_as_unicode())
        for locations in results["locations"]:
            properties = {
                'addr_full': locations['location']['address1'],
                'city': locations['location']['city'],
                'state': locations['location']['state'],
                'phone': locations['location']['phone'],
                'website': locations['location']['localPageURL'],
                'ref': locations['location']['rlid'],
                'lon':float(locations['location']['longitude']),
                'lat':float(locations['location']['latitude']),
            }

            yield GeojsonPointItem(**properties)