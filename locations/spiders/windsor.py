# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem


class FiestaMartSpider(scrapy.Spider):
    name = "windsor"
    item_attributes = {"brand": "Windsor", "brand_wikidata": "Q72981668"}
    allowed_domains = ["windsorstore.com"]
    start_urls = [
        "https://www.windsorstore.com/pages/locations",
    ]

    def start_requests(self):
        template = "https://cdn.shopify.com/s/files/1/0070/8853/7651/t/8/assets/stores.json?1617387302848"

        headers = {
            "Accept": "application/json",
        }

        yield scrapy.http.FormRequest(
            url=template, method="GET", headers=headers, callback=self.parse
        )

    def parse(self, response):
        jsonresponse = response.json()
        for stores in jsonresponse["features"]:
            store = json.dumps(stores)
            store_data = json.loads(store)

            properties = {
                "name": store_data["properties"]["name"],
                "ref": store_data["properties"]["id"],
                "addr_full": store_data["properties"]["street_1"],
                "city": store_data["properties"]["city"],
                "state": store_data["properties"]["state"],
                "postcode": store_data["properties"]["zip"],
                "phone": store_data["properties"]["phone"],
                "lat": float(store_data["geometry"]["coordinates"][0]),
                "lon": float(store_data["geometry"]["coordinates"][1]),
                "website": store_data.get("url"),
            }

            yield GeojsonPointItem(**properties)
