# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem


class Freebirds(scrapy.Spider):
    name = "freebirds"
    item_attributes = {"brand": "Freebirds World Burrito", "brand_wikidata": "Q5500367"}
    start_urls = [
        "https://cms.freebirds.chepri.com/fb/items/locations?fields=*.*&limit=-1"
    ]

    def parse(self, response):
        results = response.json()
        for data in results["data"]:
            props = {
                "ref": data.get("id"),
                "street_address": data.get("address_1"),
                "city": data.get("city"),
                "postcode": data.get("zip_code"),
                "state": data.get("state"),
                "website": data.get("rio_url"),
                "phone": data.get("phone_number"),
                "country": data.get("country"),
            }

            yield GeojsonPointItem(**props)
