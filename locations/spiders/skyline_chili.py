# -*- coding: utf-8 -*-
import scrapy
import json

from locations.hours import OpeningHours, DAYS
from locations.items import GeojsonPointItem


class SkylineChiliSpider(scrapy.Spider):
    name = "skyline_chili"
    item_attributes = {
        "name": "Skyline Chili",
        "brand": "Skyline Chili",
        "brand_wikidata": "Q151224",
    }

    allowed_domains = ["skylinechili.com"]
    start_urls = ("https://locations.skylinechili.com/sitemap.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        store_urls = response.xpath("//*/loc/text()").extract()
        for url in store_urls:
            yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        data = json.loads(
            response.xpath('//*/script[@type="application/ld+json"]/text()').get()
        )
        properties = {
            "ref": data["@id"],
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "lon": data["geo"]["longitude"],
            "lat": data["geo"]["latitude"],
            "phone": data.get("telephone"),
            "website": data["url"],
            "opening_hours": self.parse_hours(
                data.get("openingHoursSpecification", [])
            ),
        }
        yield GeojsonPointItem(**properties)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for spec in hours:
            if {"dayOfWeek", "closes", "opens"} <= spec.keys():
                opening_hours.add_range(
                    spec["dayOfWeek"][:2], spec["opens"], spec["closes"]
                )
            elif {"opens", "closes"} <= spec.keys():
                for day in DAYS:
                    opening_hours.add_range(day, spec["opens"], spec["closes"])
            else:
                continue
        return opening_hours.as_opening_hours()
