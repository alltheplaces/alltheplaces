# -*- coding: utf-8 -*-
import re
import json

import scrapy

from locations.items import GeojsonPointItem


class MillerCarterSpider(scrapy.Spider):
    # download_delay = 0.2
    name = "millercarter"
    item_attributes = {"brand": "Miller and Carter"}
    allowed_domains = ["millerandcarter.co.uk"]
    start_urls = ("https://www.millerandcarter.co.uk/ourvenues#/",)

    def parse(self, response):
        urls = response.xpath('//div[@class="accordion parbase section"]//a/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_place)

    def parse_place(self, response):
        data = json.loads(response.xpath('//script[@type="application/ld+json" and contains(text(), "GeoCoordinates")]/text()').extract_first())

        properties = {
            "name": data["name"],
            "ref": data["@id"],
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"],
            "phone": data.get("telephone"),
            "website": response.url,
            "lat": float(data["geo"]["latitude"]),
            "lon": float(data["geo"]["longitude"]),
        }

        yield GeojsonPointItem(**properties)
