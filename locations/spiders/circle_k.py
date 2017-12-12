# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class CircleKSpider(scrapy.Spider):

    name = "circle_k"
    allowed_domains = ["www.circlek.com"]
    start_urls = (
        'https://www.circlek.com/copy_new_stores.php?lat=36.70099&lng=-95.93642399999999&distance=16000&services=',
    )

    def parse(self, response):
        results = json.loads(response.body_as_unicode())
        for data in results:
            properties = {
                'ref': data['id'],
                'lat': float(data['latitude']) if data['latitude'] else None,
                'lon': float(data['longitude']) if data['longitude'] else None,
                'addr_full': data['address'],
                'website': 'https://www.circlek.com/store-locator/us/{}/{}/{}'.format(
                    data['city'].lower(),
                    data['address'].lower().replace(' ', '-'),
                    data['cost_center'],
                ),
                'city': data['city'],
            }

            yield GeojsonPointItem(**properties)
