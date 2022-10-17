# -*- coding: utf-8 -*-
import scrapy
import json

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class Tillys(scrapy.Spider):
    name = "tillys"
    item_attributes = {"brand": "Tillys", "brand_wikidata": "Q7802889"}
    start_urls = [
        "https://www.tillys.com/on/demandware.store/Sites-tillys-Site/default/Stores-FindStores?showMap=false&isAjax=false&location=66952&radius=10000"
    ]

    def parse(self, response):
        results = response.json()
        for data in results["stores"]:

            props = {
                "ref": data.get("ID"),
                "name": data.get("name"),
                "street_address": data.get("address1"),
                "city": data.get("city"),
                "postcode": data.get("postalCode"),
                "state": data.get("stateCode"),
                "phone": data.get("phone"),
                "country": data.get("countryCode"),
                "lat": data.get("latitude"),
                "lon": data.get("longitude"),
            }

            yield GeojsonPointItem(**props)
