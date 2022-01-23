# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class AlbertHeijnSpider(scrapy.Spider):
    name = "albert_heijn"
    item_attributes = {"brand": "Albert Heijn", "brand_wikidata": "Q1653985"}
    allowed_domains = ["www.ah.nl", "www.ah.be"]
    start_urls = (
        "https://www.ah.nl/sitemaps/entities/stores/stores.xml",
        "https://www.ah.be/sitemaps/entities/stores/stores.xml",
    )

    def parse(self, response):
        response.selector.remove_namespaces()
        for url in response.xpath("//loc/text()").extract():
            if re.search("/winkel/albert-heijn/", url):
                yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        for ldjson in response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).extract():
            data = json.loads(ldjson)
            if data["@type"] != "GroceryStore":
                continue

            opening_hours = OpeningHours()
            for spec in data["openingHoursSpecification"]:
                opening_hours.add_range(
                    spec["dayOfWeek"][:2], spec["opens"], spec["closes"]
                )

            properties = {
                "ref": response.url,
                "website": response.url,
                "name": data["name"],
                "phone": data["telephone"],
                "lat": data["geo"]["latitude"],
                "lon": data["geo"]["longitude"],
                "addr_full": data["address"]["streetAddress"],
                "city": data["address"]["addressLocality"],
                "postcode": data["address"]["postalCode"],
                "country": data["address"]["addressCountry"],
                "opening_hours": opening_hours.as_opening_hours(),
            }
            yield GeojsonPointItem(**properties)
