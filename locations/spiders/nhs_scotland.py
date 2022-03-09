# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem


class NHSScotlandSpider(scrapy.Spider):
    name = "nhsscotland"
    item_attributes = {"brand": "NHS Scotland"}
    allowed_domains = ["nhsinform.scot"]
    start_urls = ("https://www.nhsinform.scot/scotlands-service-directory",)

    def parse(self, response):
        urls = response.xpath(
            '//div[@class="js-equal-height blockgrid-list"]/a/@href'
        ).extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_directory)

    def parse_directory(self, response):
        directory_urls = response.xpath(
            '//ul[@class="search__results"]/li/div/h3/a/@href'
        ).extract()

        for url in directory_urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):

        try:
            geo = response.xpath(
                '//div[@class="cf bg-light-grey-1 soft-half"]/a/@href'
            ).extract_first()
            coords = re.search(r".+/(.+?)/?(?:\.html|$)", geo).group(1)
            lat = coords.split(",")[0]
            lon = coords.split(",")[1]
            addressfull = response.xpath(
                '//address[@class="beta dark-grey-3 push-half--bottom"]/text()'
            ).extract()
            add1 = [x.rstrip() for x in addressfull]
            add2 = [x.lstrip() for x in add1]
            address = " ".join(str(e) for e in add2)

            properties = {
                "ref": response.xpath('//h1[@class="giga bold primary-color"]/text()')
                .extract_first()
                .strip()
                + " "
                + response.xpath(
                    '//address[@class="beta dark-grey-3 push-half--bottom"]/text()'
                )
                .extract()[2]
                .strip(),
                "name": response.xpath('//h1[@class="giga bold primary-color"]/text()')
                .extract_first()
                .strip(),
                "addr_full": address.strip(),
                "country": re.search(r".+/?google.co.(.+?)/", geo).group(1),
                "lat": float(lat),
                "lon": float(lon),
                "website": response.url,
            }
            yield GeojsonPointItem(**properties)

        except:
            pass
