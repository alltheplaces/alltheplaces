# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem


class Ridleys(scrapy.Spider):
    name = "ridleys"
    item_attributes = {"brand": "Ridley's Family Markets"}
    start_urls = ["https://shopridleys.com/_ajax_map.php"]

    def parse(self, response):
        results = response.json()
        for data in results:
            props = {
                "ref": data.get("storeNumber"),
                "street_address": data.get("streetAddress"),
                "name": data.get("storeName"),
                "city": data.get("city"),
                "postcode": data.get("zip"),
                "state": data.get("state"),
                "website": data.get("rio_url"),
                "phone": data.get("phone"),
                "lat": data.get("lat"),
                "lon": data.get("lon"),
                "country": "US",
            }

            yield GeojsonPointItem(**props)
