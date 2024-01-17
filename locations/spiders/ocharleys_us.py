# -*- coding: utf-8 -*-

import scrapy

from locations.items import Feature


class OcharleysUSSpider(scrapy.Spider):
    name = "ocharleys_us"
    item_attributes = {"brand": "O'Charley's", "brand_wikidata": "Q7071703"}
    allowed_domains = ["ocharleys.com"]
    start_urls = [
        "https://orderback.ocharleys.com:8081/restaurants",
    ]

    def parse(self, response):
        data = response.json()

        for place in data["restaurants"]:
            properties = {
                "name": place["storename"],
                "ref": place["extref"],
                "street_address": place["streetaddress"],
                "city": place["city"],
                "state": place["state"],
                "postcode": place["zip"],
                "country": place["country"],
                "phone": place["telephone"],
                "lat": place["latitude"],
                "lon": place["longitude"],
                "website": place["url"],
            }

            yield Feature(**properties)
