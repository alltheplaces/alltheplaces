# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem


class Freebirds(scrapy.Spider):
    name = "freebirds"
    item_attributes = {"brand": "Freebirds World Burrito", "brand_wikidata": "Q5500367"}
    start_urls = ["https://www.freebirds.com/api/restaurants?includePrivate=false"]

    def parse(self, response):
        results = response.json()
        for data in results["restaurants"]:
            props = {
                "ref": data.get("id"),
                "street_address": data.get("streetaddress"),
                "city": data.get("city"),
                "name": data.get("name"),
                "postcode": data.get("zip"),
                "state": data.get("state"),
                "phone": data.get("telephone"),
                "country": "US",
                "lat": data.get("latitude"),
                "lon": data.get("longitude"),
            }

            yield GeojsonPointItem(**props)
