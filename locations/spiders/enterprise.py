# -*- coding: utf-8 -*-
import scrapy
import json
import logging
from locations.items import GeojsonPointItem

class EnterpriseSpider(scrapy.Spider):
    name = "enterprise"
    allowed_domains = ["enterprise.com"]
    start_urls = (
        'https://www.enterprise.com/en/car-rental/locations.html',
    )

    def parse(self, response):
        data = response.xpath('//script[@type="application/ld+json"]/text()').extract_first()
        if data:
            data = json.loads(data)
            address = data.get('address', {})
            properties = {
                'name': data.get('name'),
                'phone': data.get('telephone'),
                'website': response.url,
                'addr_full': address.get('streetAddress'),
                'city': address.get('addressLocality'),
                'state': address.get('addressRegion'),
                'postcode': address.get('postalCode'),
                'country': address.get('addressCountry'),
            }
            lat = data.get('geo', {}).get('latitude')
            lon = data.get('geo', {}).get('longitude')
            if lat: lat = float(lat)
            if lon: lon = float(lon)
            properties['lat'] = lat
            properties['lon'] = lon
            properties['ref'] = response.url
            yield GeojsonPointItem(**properties)
        else:
            for url in response.xpath('//section[contains(@class, "region-list") or contains(@class, "location-band")]//ul/li/a/@href').extract():
                yield scrapy.Request(
                    response.urljoin(url),
                    callback=self.parse,
                )

