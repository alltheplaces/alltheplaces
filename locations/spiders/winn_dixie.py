# -*- coding: utf-8 -*-

import scrapy

from locations.items import GeojsonPointItem


class FiestaMartSpider(scrapy.Spider):
    name = "winndixie"
    item_attributes = {"brand": "Winn Dixie", "brand_wikidata": "Q1264366"}
    allowed_domains = ["winndixie.com"]
    start_urls = [
        "https://www.winndixie.com/locator",
    ]

    def start_requests(self):
        template = "https://www.winndixie.com/V2/storelocator/getStores?search=jacksonville,%20fl&strDefaultMiles=1000&filter="

        headers = {
            "Accept": "application/json",
        }

        yield scrapy.http.FormRequest(
            url=template, method="GET", headers=headers, callback=self.parse
        )

    def parse(self, response):
        jsonresponse = response.json()
        for store in jsonresponse:
            properties = {
                "name": store["StoreName"],
                "ref": store["StoreCode"],
                "addr_full": store["Address"]["AddressLine2"],
                "city": store["Address"]["City"],
                "state": store["Address"]["State"],
                "postcode": store["Address"]["Zipcode"],
                "country": store["Address"]["Country"],
                "phone": store["Phone"],
                "lat": float(store["Address"]["Latitude"]),
                "lon": float(store["Address"]["Longitude"]),
                "website": response.url,
            }

            yield GeojsonPointItem(**properties)
