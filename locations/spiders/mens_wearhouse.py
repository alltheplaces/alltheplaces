# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class MensWearhouseSpider(scrapy.Spider):
    name = "mens_wearhouse"
    item_attributes = {"brand": "Men's Wearhouse"}
    allowed_domains = ["menswearhouse.com"]
    start_urls = [
        "https://www.menswearhouse.com/store-locator/directory",
    ]

    def parse_store(self, response):
        address2 = response.xpath(
            '//span[@itemprop="addressRegion"]/text()'
        ).extract_first()
        city, statezip = address2.split(",")
        state, zip = statezip.strip().split(" ")

        properties = {
            "ref": response.url,
            "name": response.xpath('//h1[@itemprop="name"]/text()').extract_first(),
            "addr_full": response.xpath(
                '//span[@itemprop="streetAddress"]/text()'
            ).extract_first(),
            "city": city,
            "state": state,
            "postcode": zip,
            "phone": response.xpath(
                '//span[@itemprop="telephone"]/text()'
            ).extract_first(),
            "website": response.url,
            "opening_hours": response.xpath(
                '//time[@itemprop="openingHours"]/@datetime'
            ).extract(),
        }

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath('//li[@class="directory__state-item"]/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
