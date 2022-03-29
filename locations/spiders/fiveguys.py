# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class FiveguysSpider(scrapy.Spider):
    name = "fiveguys"
    item_attributes = {"brand": "Five Guys", "brand_wikidata": "Q1131810"}
    allowed_domains = ["www.fiveguys.com"]
    start_urls = (
        "http://www.fiveguys.com/5gapi/stores/ByDistance?lat=45.0&lng=-90.0&distance=25000&secondaryDistance=250&lang=en",
    )

    def parse(self, response):
        results = response.json()

        for store_data in results:
            properties = {
                "phone": store_data["PhoneNumber"],
                "addr_full": store_data["AddressLine1"],
                "city": store_data["City"],
                "state": store_data["StateOrProvince"],
                "postcode": store_data["PostalCode"],
                "country": store_data["Country"],
                "ref": store_data["ClientKey"],
                "name": store_data["LocationName"],
                "lon": float(store_data["Longitude"]),
                "lat": float(store_data["Latitude"]),
            }

            yield GeojsonPointItem(**properties)
