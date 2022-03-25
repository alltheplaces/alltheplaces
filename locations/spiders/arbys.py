# -*- coding: utf-8 -*-
import json
import re
import scrapy
from locations.items import GeojsonPointItem


class ArbysSpider(scrapy.Spider):

    name = "arby"
    item_attributes = {"brand": "Arby's", "brand_wikidata": "Q630866"}
    allowed_domains = ["locations.arbys.com"]
    download_delay = 0.2
    start_urls = ("https://locations.arbys.com/",)

    def get_store_info(self, response):
        data = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).extract_first()
        if data:
            try:
                data = json.loads(data)[0]
            except json.JSONDecodeError:
                # Unescaped " on two pages
                lines = data.split("\n")
                i = 2 + next(
                    i for (i, line) in enumerate(lines) if "mainContentOfPage" in line
                )
                lines[i] = '"text": ""}'
                data = "\n".join(lines)
                data = json.loads(data)[0]

            properties = {
                "ref": response.css("div.store-id::text").get().split(": ")[-1],
                "name": data["name"],
                "addr_full": data["address"]["streetAddress"].strip(),
                "city": data["address"]["addressLocality"].strip(),
                "state": data["address"]["addressRegion"],
                "postcode": data["address"]["postalCode"],
                "phone": data["address"]["telephone"],
                "lat": float(data["geo"]["latitude"]),
                "lon": float(data["geo"]["longitude"]),
                "website": response.url,
                "opening_hours": data["openingHours"],
            }

            yield GeojsonPointItem(**properties)

    def parse_store(self, response):
        city_stores = response.xpath(
            '//a[@class="location-name ga-link"]/@href'
        ).extract()
        for city_store in city_stores:
            yield scrapy.Request(
                response.urljoin(city_store), callback=self.get_store_info
            )

    def parse_state(self, response):

        cities = response.xpath('//a[@class="ga-link"]/@href').extract()
        for city in cities:
            yield scrapy.Request(response.urljoin(city), callback=self.parse_store)

    def parse(self, response):
        states = response.xpath('//a[@class="ga-link"]/@href').extract()

        for state in states:
            yield scrapy.Request(response.urljoin(state), callback=self.parse_state)
