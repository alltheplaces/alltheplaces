# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class ValvolineInstantOilChangeSpider(scrapy.Spider):
    name = "valvoline_instant_oil_change"
    item_attributes = {
        "brand": "Valvoline Instant Oil Change",
        "brand_wikidata": "Q7912852",
    }
    allowed_domains = ["vioc.com"]
    start_urls = [
        "https://store.vioc.com/",
    ]

    def parse(self, response):
        state_urls = response.xpath(
            '//*[@class="map-list-item is-single"]/strong/a/@href'
        ).extract()
        for path in state_urls:
            yield scrapy.Request(
                url=path,
                callback=self.parse_cities,
            )

    def parse_cities(self, response):
        city_urls = response.xpath(
            '//*[@class="map-list-item is-single"]/strong/a/@href'
        ).extract()
        for path in city_urls:
            yield scrapy.Request(
                url=path,
                callback=self.parse_stores,
            )

    def parse_stores(self, response):
        place_urls = response.xpath(
            '//*[@class="location-name-wrap"]/a/@href'
        ).extract()
        for path in place_urls:
            yield scrapy.Request(
                url=path,
                callback=self.parse_store,
            )

    def parse_store(self, response):
        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json"]/text()'
            ).extract_first()
        )

        properties = {
            "ref": "_".join(
                re.search(r".+/(.+?)/(.+?)/?(?:\.html|$)", response.url).groups()
            ),
            "name": response.xpath('//*[@class="indy-info"]/h1/text()').extract_first(),
            "addr_full": data[0]["address"]["streetAddress"],
            "city": data[0]["address"]["addressLocality"],
            "state": data[0]["address"]["addressRegion"],
            "postcode": data[0]["address"]["postalCode"],
            "country": "US",
            "lat": data[0]["geo"]["latitude"],
            "lon": data[0]["geo"]["longitude"],
            "phone": data[0]["address"]["telephone"],
            "website": data[0]["url"],
        }

        yield GeojsonPointItem(**properties)
