# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class PortillosSpider(scrapy.Spider):
    name = "portillos"
    allowed_domains = ["www.portillos.com"]
    start_urls = (
        'https://www.portillos.com/locations/',
    )

    def parse(self, response):
        yield scrapy.Request(
            'https://www.portillos.com/ajax/location/getAllLocations/',
            callback=self.parse_locations,
            method='POST',
            body='{"locations":[],"all":"y"}',
            headers={
                'Content-Type': 'application/json;charset=UTF-8',
                'Accept': 'application/json',
                's': 'mjA1AiWID8JqImr3iMoEXFUpeuasRBIglY+FBqETplI=',
            }
        )

    def parse_locations(self, response):
        data = json.loads(response.body_as_unicode())

        for location in data['locations']:
            yield scrapy.Request(
                'https://www.portillos.com/ajax/location/getLocationDetails/?id=' + location['Id'],
                callback=self.parse_store,
            )

    def parse_store(self, response):
        store_data = json.loads(response.body_as_unicode())

        properties = {
            'phone': store_data['Phone'],
            'website': response.urljoin(store_data['Url']),
            'ref': store_data['Id'],
            'name': store_data['Name'],
            'addr:full': store_data['Address'],
            'addr:postcode': store_data['Zip'],
            'addr:state': store_data['State'],
            'addr:city': store_data['City'],
        }

        lon_lat = [
            float(store_data['Lng']),
            float(store_data['Lat']),
        ]

        yield GeojsonPointItem(
            properties=properties,
            lon_lat=lon_lat,
        )
