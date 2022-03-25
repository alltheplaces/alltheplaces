# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem


class CostaCoffeeSpider(scrapy.Spider):
    name = "costacoffee"
    item_attributes = {"brand": "Costa Coffee"}
    allowed_domains = ["costa.co.uk/"]
    start_urls = [
        "https://www.costa.co.uk/locations/store-locator",
    ]

    def start_requests(self):
        template = "https://www.costa.co.uk/api/locations/stores?latitude=51.46760999999998&longitude=-0.1583477000000073&maxrec=600"

        headers = {
            "Accept": "application/json",
        }

        yield scrapy.http.FormRequest(
            url=template, method="GET", headers=headers, callback=self.parse
        )

    def parse(self, response):
        jsonresponse = json.loads(response.body_as_unicode())
        for stores in jsonresponse["stores"]:
            store = json.dumps(stores)
            store_data = json.loads(store)
            addr_full = (
                store_data["storeAddress"]["addressLine1"]
                + " "
                + store_data["storeAddress"]["addressLine2"]
                + " "
                + store_data["storeAddress"]["addressLine2"]
            )

            properties = {
                "ref": store_data["storeNo8Digit"],
                "name": store_data["storeNameExternal"],
                "addr_full": addr_full.strip(),
                "city": store_data["storeAddress"]["city"],
                "postcode": store_data["storeAddress"]["postCode"],
                "country": store_data["storeAddress"]["country"],
                "lat": float(store_data["latitude"]),
                "lon": float(store_data["longitude"]),
            }

            yield GeojsonPointItem(**properties)
