# -*- coding: utf-8 -*-
import json
import urllib.parse

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class AwrestaurantsSpider(scrapy.Spider):
    name = "awrestaurants"
    item_attributes = {"brand": "A&W Restaurants", "brand_wikidata": "Q277641"}
    allowed_domains = ["awrestaurants.com"]
    start_urls = ("https://awrestaurants.com/sitemap.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        for url in response.xpath("//loc/text()").extract():
            if "/locations/" in url:
                # Rewrite from staging domain…
                path = urllib.parse.urlparse(url).path
                yield scrapy.Request(response.urljoin(path), callback=self.parse_store)

    def parse_store(self, response):
        data = json.loads(
            response.xpath('//script[@type="application/ld+json"]/text()').get()
        )

        hours = OpeningHours()
        for row in data["openingHoursSpecification"]:
            if {"opens", "closes"} <= row.keys():
                day = row["dayOfWeek"].lstrip("https://schema.org/")[:2]
                hours.add_range(day, row["opens"], row["closes"], "%H:%M:%S")

        properties = {
            "ref": response.url,
            "website": response.url,
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "name": data["name"],
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "phone": data["telephone"],
            "opening_hours": hours.as_opening_hours(),
        }
        return GeojsonPointItem(**properties)
