# -*- coding: utf-8 -*-
import json
import scrapy
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class AppleSpider(scrapy.Spider):
    name = "apple"
    item_attributes = {"brand": "Apple", "brand_wikidata": "Q421253"}
    allowed_domains = ["apple.com"]
    start_urls = ("https://www.apple.com/retail/sitemap/sitemap.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        for url in response.xpath("//loc/text()").extract():
            url = url.strip()
            yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        ldjson = json.loads(
            response.css('script[type="application/ld+json"]::text').get()
        )

        opening_hours = OpeningHours()
        for spec in ldjson["openingHoursSpecification"]:
            if not spec.keys() >= {"dayOfWeek", "opens", "closes"}:
                continue
            for day in spec["dayOfWeek"]:
                opening_hours.add_range(day[:2], spec["opens"], spec["closes"])

        properties = {
            "website": response.url,
            "ref": ldjson["branchCode"],
            "lat": ldjson["geo"]["latitude"],
            "lon": ldjson["geo"]["longitude"],
            "name": ldjson["name"],
            "phone": ldjson["telephone"],
            "addr_full": ldjson["address"]["streetAddress"],
            "city": ldjson["address"]["addressLocality"],
            "state": ldjson["address"]["addressRegion"],
            "postcode": ldjson["address"]["postalCode"],
            "opening_hours": opening_hours.as_opening_hours(),
        }

        yield GeojsonPointItem(**properties)
