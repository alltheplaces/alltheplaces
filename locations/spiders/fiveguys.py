# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class FiveguysSpider(scrapy.Spider):
    name = "fiveguys"
    allowed_domains = ["www.fiveguys.com"]
    start_urls = (
        'http://www.fiveguys.com/5gapi/stores/ByDistance?lat=45.0&lng=-90.0&distance=25000&secondaryDistance=250&lang=en',
    )

    def parse(self, response):
        results = json.loads(response.body_as_unicode())

        for data in results:
            store_data = data['Store']

            properties = {
                'phone': store_data['PhoneNumber'],
                'addr:full': store_data['AddressLine1'],
                'addr:city': store_data['City'],
                'addr:state': store_data['StateOrProvince'],
                'addr:postcode': store_data['PostalCode'],
                'ref': store_data['ClientKey'],
            }

            lon_lat = [
                float(store_data['Longitude']),
                float(store_data['Latitude']),
            ]

            yield GeojsonPointItem(
                properties=properties,
                lon_lat=lon_lat,
            )
