# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem


class PotbellySandwichSpider(scrapy.Spider):

    name = "potbelly_sandwich"
    allowed_domains = ["www.potbelly.com"]
    start_urls = (
        'https://api-origin.potbelly.com/proxy/v15/apps/1055/locations?lat=41.8781136&lng=-87.62979819999998&fulfillment_types=pickup&has_breakfast=false&in_delivery_area=false',
    )

    def start_requests(self):

        url = self.start_urls[0]

        headers = {
                   'Accept': 'application/json, text/plain, */*',
                   'Accept-Language': 'en-US,en;q=0.9,ru;q=0.6',
                   'Origin': 'https://www.potbelly.com',
                   'Accept-Encoding': 'gzip, deflate, br',
                   'Referer': 'https://www.potbelly.com/store-locator',
                   'Connection': 'keep-alive',
                   }

        url = self.start_urls[0]

        yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def parse(self, response):
        results = json.loads(response.body_as_unicode())
        for data in results:
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
