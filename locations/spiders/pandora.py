# -*- coding: utf-8 -*-
import scrapy
import re
import json

from locations.items import GeojsonPointItem


class PandoraSpider(scrapy.Spider):
    name = "pandora"
    item_attributes = {"brand": "Pandora"}
    allowed_domains = ["pandora.net"]
    start_urls = ("https://stores.pandora.net/en-us/",)

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath(
            '//div[@class="map-list-item is-single"]/a/@href'
        ).extract()
        for path in city_urls:
            yield scrapy.Request(
                response.request.url + path.strip(),
                callback=self.parse_state,
            )

    def parse_state(self, response):
        response.selector.remove_namespaces()
        location_urls = response.xpath(
            '//div[@class="map-list-item is-single"]/a[@class="gaq-link"]/@href'
        ).extract()
        for path in location_urls:
            yield scrapy.Request(
                response.request.url + path.strip(),
                callback=self.parse_city,
            )

    def parse_city(self, response):
        response.selector.remove_namespaces()
        location_urls = response.xpath(
            '//a[@class="js-view-store-details gaq-link"]/@href'
        ).extract()
        for path in location_urls:
            yield scrapy.Request(
                "https:" + path.strip(),
                callback=self.parse_store,
            )

    def parse_store(self, response):
        json_data = (
            response.xpath('//script[@type="application/ld+json"]/text()')
            .extract_first()
            .replace('"Chic"', "Chic")
        )
        data = json.loads(json_data)
        data = data[0]

        properties = {
            "name": data["name"],
            "ref": data["name"],
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "phone": data["address"]["telephone"],
            "website": data["url"],
            "opening_hours": data["openingHours"],
            "lat": float(data["geo"]["latitude"]),
            "lon": float(data["geo"]["longitude"]),
        }

        yield GeojsonPointItem(**properties)
