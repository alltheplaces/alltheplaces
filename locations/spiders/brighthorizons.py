# -*- coding: utf-8 -*-
import json
import logging
import re
import time

from locations.items import GeojsonPointItem
from scrapy.spiders import SitemapSpider


class BrightHorizonsSpider(SitemapSpider):
    name = "brighthorizons"
    item_attributes = {
        "brand": "Bright Horizons",
        "brand_wikidata": "Q4967421",
        "country": "US",
    }
    allowed_domains = ["brighthorizons.com"]
    sitemap_urls = ["https://child-care-preschool.brighthorizons.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/child-care-preschool\.brighthorizons\.com\/(\w{2})\/(\w+)\/([-\w]+)$",
            "parse_store",
        )
    ]

    def sitemap_filter(self, entries):
        for entry in entries:
            match = re.match(self.sitemap_rules[0][0], entry["loc"])
            if match:
                if match.group(1) == "ZZ":
                    # ZZ is there testing data
                    continue
                yield entry

    def parse_store(self, response):

        if response.xpath('//a[@itemprop="telephone"]/text()').extract_first():
            telephoneNumber = (
                response.xpath('//a[@itemprop="telephone"]/text()')
                .extract_first()
                .strip()
            )
        else:
            telephoneNumber = response.xpath(
                '//a[@itemprop="telephone"]/text()'
            ).extract_first()

        if response.xpath(
            '//div/section/ul/li/meta[@itemprop="openingHours"]/@content'
        ).extract_first():
            storeHours = (
                response.xpath(
                    '//div/section/ul/li/meta[@itemprop="openingHours"]/@content'
                )
                .extract_first()
                .strip()
            )
        else:
            storeHours = response.xpath(
                '//div/section/ul/li/meta[@itemprop="openingHours"]/@content'
            ).extract_first()

        properties = {
            "name": response.xpath("//h1/text()").extract_first(),
            "ref": response.xpath("//h1/text()").extract_first(),
            "addr_full": response.xpath(
                '//span[@itemprop="streetAddress"]/text()'
            ).extract_first(),
            "city": response.xpath(
                '//span[@itemprop="addressLocality"]/text()'
            ).extract_first(),
            "state": response.xpath(
                '//span[@itemprop="addressRegion"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                '//span[@itemprop="postalCode"]/text()'
            ).extract_first(),
            "phone": telephoneNumber,
            "website": response.request.url,
            "opening_hours": storeHours,
            "lat": float(
                response.xpath(
                    '//div/meta[@itemprop="latitude"]/@content'
                ).extract_first()
            ),
            "lon": float(
                response.xpath(
                    '//div/meta[@itemprop="longitude"]/@content'
                ).extract_first()
            ),
        }

        yield GeojsonPointItem(**properties)
