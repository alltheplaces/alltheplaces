# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class AccentureSpider(scrapy.Spider):
    name = "accenture"
    item_attributes = {'brand': "Accenture"}
    allowed_domains = ["accenture.com"]
    start_urls = [
        'https://www.accenture.com/us-en/about/locations/office-details?loc=United%20States',
    ]

    def start_requests(self):
        template = 'https://www.accenture.com/api/sitecore/LocationsHeroModule/GetLocation?query=United%20States&from=0&size=150&language=en'

        headers = {
            'Accept': 'application/json',
        }

        yield scrapy.http.FormRequest(
            url=template,
            method='GET',
            headers=headers,
            callback=self.parse
        )

    def parse(self, response):
        jsonresponse = json.loads(response.body_as_unicode())
        data = jsonresponse["documents"]
        for stores in data:
            store = json.dumps(stores)
            store_data = json.loads(store)

            properties = {
                'name': store_data["LocationName"],
                'ref': store_data["LocationName"],
                'addr_full': store_data["Address"],
                'city': store_data["CityName"],
                'state': store_data["StateCode"],
                'postcode': store_data["PostalZipCode"],
                'country': store_data["Country"],
                'phone': store_data.get("ContactTel"),
                'lat': float(store_data["Latitude"]),
                'lon': float(store_data["Longitude"]),
                'website': store_data.get("LocationURL")
            }

            yield GeojsonPointItem(**properties)