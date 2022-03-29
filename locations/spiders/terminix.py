# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem


class TerminixSpider(scrapy.Spider):
    # download_delay = 0.2
    name = "terminix"
    item_attributes = {"brand": "Terminix", "brand_wikidata": "Q7702831"}
    allowed_domains = ["terminix.com"]
    start_urls = ("https://www.terminix.com/exterminators/",)

    def parse(self, response):
        urls = response.xpath(
            '//*[@id="state-list"]/div[3]/div[3]/div//ul//a/@href'
        ).extract()

        for url in urls:
            st = url[:2]
            yield scrapy.Request(response.urljoin(st), callback=self.parse_state)

    def parse_state(self, response):
        cityurls = response.xpath('//*[@id="content"]/div/div/div//a/@href').extract()

        for city in cityurls:
            store = city[2:]
            yield scrapy.Request(response.urljoin(city), callback=self.parse_store)

    def parse_store(self, response):

        try:
            phone = response.xpath(
                '//span[@class="Phone Phone--desktop"]/text()'
            ).extract()[0]
        except:
            phone = ""

        properties = {
            "ref": response.url,
            "name": response.xpath('//h3[@class="NAP-locationName"]/text()').extract()[
                0
            ],
            "addr_full": response.xpath(
                '//span[@itemprop="streetAddress"]/text()'
            ).extract()[0],
            "city": response.xpath(
                '//span[@itemprop="addressLocality"]/text()'
            ).extract()[0],
            "state": response.xpath(
                '//span[@itemprop="addressRegion"]/text()'
            ).extract()[0],
            "postcode": response.xpath(
                '//span[@itemprop="postalCode"]/text()'
            ).extract()[0],
            "country": response.xpath(
                '//span[@itemprop="addressCountry"]/text()'
            ).extract()[0],
            "phone": phone,
            "lat": float(
                response.xpath(
                    '//span[@class="coordinates"]/meta[1]/@content'
                ).extract()[0]
            ),
            "lon": float(
                response.xpath(
                    '//span[@class="coordinates"]/meta[2]/@content'
                ).extract()[0]
            ),
        }

        yield GeojsonPointItem(**properties)
