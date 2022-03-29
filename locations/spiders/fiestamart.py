# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem


class FiestaMartSpider(scrapy.Spider):
    name = "fiestamart"
    item_attributes = {"brand": "Fiesta Mart"}
    allowed_domains = ["fiestamart.com"]
    start_urls = [
        "https://www.fiestamart.com/store-locator/",
    ]

    def start_requests(self):
        template = "https://www.fiestamart.com/wp-json/store_locations/all"

        headers = {
            "Accept": "application/json",
        }

        yield scrapy.http.FormRequest(
            url=template, method="GET", headers=headers, callback=self.parse
        )

    def parse(self, response):
        jsonresponse = response.json()
        for stores in jsonresponse["locations"]:
            store = json.dumps(stores)
            store_data = json.loads(store)

            properties = {
                "name": store_data["name"],
                "ref": store_data["id"],
                "addr_full": store_data["address"],
                "city": store_data["city"],
                "state": store_data["state"],
                "postcode": store_data["postal"],
                "phone": store_data["phone"],
                "lat": float(store_data["lat"]),
                "lon": float(store_data["lng"]),
                "website": response.url,
            }

            yield GeojsonPointItem(**properties)
