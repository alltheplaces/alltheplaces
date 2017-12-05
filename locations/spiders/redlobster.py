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
        for locations in results["locations"]:
            properties = {
                'phone': locations['location']['phone'],
                'addr:full': locations['location']['address1'],
                'addr:city': locations['location']['city'],
                'website': locations['location']['localPageURL'],
                'ref': locations['location']['rlid'],
                'lon':locations['location']['longitude'],
                'lat':locations['location']['latitude'],
            }

            lon_lat = [
                locations['location']['longitude'],
                locations['location']['latitude'],
            ]

            yield GeojsonPointItem(
                properties=properties,
                lon_lat=lon_lat,
            )