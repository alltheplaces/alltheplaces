# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class CarrefourFrSpider(scrapy.Spider):
    name = "carrefour_fr"
    item_attributes = {"brand": "Carrefour"}
    allowed_domains = ["carrefour.com"]

    def start_requests(self):
        urls = [
            "https://www.carrefour.fr/magasin/liste",
            "https://www.carrefour.fr/magasin/liste/market",
            "https://www.carrefour.fr/magasin/liste/city",
            "https://www.carrefour.fr/magasin/liste/bio",
            "https://www.carrefour.fr/magasin/liste/contact",
            "https://www.carrefour.fr/magasin/liste/montagne",
            "https://www.carrefour.fr/magasin/liste/bon-app",
        ]

        for url in urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
            ).extract_first()
        )

        for store in data:
            properties = {
                "ref": store["@id"],
                "name": store["name"],
                "addr_full": store["address"]["streetAddress"],
                "city": store["address"]["addressLocality"],
                "state": store["address"]["addressRegion"],
                "postcode": store["address"]["postalCode"],
                "country": store["address"]["addressCountry"],
                "lat": store["geo"]["latitude"],
                "lon": store["geo"]["longitude"],
            }

            yield GeojsonPointItem(**properties)
