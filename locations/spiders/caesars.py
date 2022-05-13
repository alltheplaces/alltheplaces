# -*- coding: utf-8 -*-

import scrapy

from locations.items import GeojsonPointItem


class CaesarsSpider(scrapy.Spider):
    name = "caesars"
    item_attributes = {"brand": "Caesars Entertainment", "brand_wikidata": "Q18636524"}
    allowed_domains = ["caesars.com"]
    start_urls = [
        "https://www.caesars.com/destinations",
    ]

    def start_requests(self):
        template = "https://www.caesars.com/api/v1/properties"

        headers = {
            "Accept": "application/json",
        }

        yield scrapy.http.FormRequest(
            url=template, method="GET", headers=headers, callback=self.parse
        )

    def parse(self, response):
        stores = response.json()
        for store in stores:

            properties = {
                "ref": store["id"],
                "name": store["name"],
                "addr_full": store.get("address").get("street"),
                "city": store.get("address").get("city"),
                "state": store.get("address").get("state"),
                "postcode": store.get("address").get("zip"),
                "country": "US",
                "phone": store.get("phone"),
                "lat": float(store["location"]["latitude"]),
                "lon": float(store["location"]["longitude"]),
                "website": store.get("url"),
                "extras": {"brand": store["brand"]},
            }

            yield GeojsonPointItem(**properties)
