# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem



class CostaCoffeeSpider(scrapy.Spider):
    name = "costacoffeeie"
    item_attributes = {'brand': "Costa Coffee"}
    allowed_domains = ["costaireland.ie"]
    start_urls = [
        'https://www.costaireland.ie/locations/store-locator/map?latitude=53.34463099999999&longitude=-6.259525999999994',
    ]

    def start_requests(self):
        template = 'https://www.costaireland.ie/api/cf/?locale=en-IE&include=2&content_type=storeV2&limit=500&fields.location[near]=53.344630999999964,-6.259525999999994'

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
        for stores in jsonresponse["items"]:
            store = json.dumps(stores)
            store_data = json.loads(store)
            data = store_data["fields"]

            properties = {
                'ref': data["storeAddress"],
                'name': data["storeName"],
                'addr_full': data["storeAddress"],
                'country': "IE",
                'lat': float(data["location"]["lat"]),
                'lon': float(data["location"]["lon"])
            }

            yield GeojsonPointItem(**properties)
