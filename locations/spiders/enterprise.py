# -*- coding: utf-8 -*-
import scrapy
import json
import logging
from locations.items import GeojsonPointItem

class EnterpriseSpider(scrapy.Spider):
    name = "enterprise"
    allowed_domains = ["www.enterprise.com"]
    start_urls = (
        'https://www.enterprise.com/en/car-rental/locations.html',
    )

    def parse(self, response):
        for u in response.xpath('//div[@class="cf"]/ul/li/a/@href').extract():
            if u.startswith('/en/car-rental/locations'):
                country = u.rsplit('/', 1)[1].rsplit('.', 1)[0]
                yield scrapy.Request(
                    'https://www.enterprise.com/en/car-rental/locations/%s/_jcr_content.mapdata.js' % country,
                    callback=self.parse_country,
                )

    def parse_country(self, response):
        data = json.loads(response.body_as_unicode())
        if data:
            for d in data:
                properties = {
                    'name': d.get('name'),
                    'phone': d.get('formatted_phone'),
                    'website': d.get('url'),
                    'addr_full': d.get('address_lines'),
                    'city': d.get('city'),
                    'state': d.get('state'),
                    'postcode': d.get('postal_code'),
                    'country': d.get('country_code'),
                    'lat': d.get('latitude'),
                    'lon': d.get('longitude'),
                    'ref': d.get('station_id'),
                }
                yield GeojsonPointItem(**properties)