# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem


class PalmBeachTanSpider(scrapy.Spider):
    name = "palm_beach_tan"
    item_attributes = {"brand": "Palm Beach Tan", "brand_wikidata": "Q64027086"}
    allowed_domains = ["palmbeachtan.com"]
    start_urls = [
        "https://palmbeachtan.com/locations/states/",
    ]
    download_delay = 0.5

    def parse(self, response):
        urls = response.xpath('//div[@class="state-list"]/ul/li/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_cities)

    def parse_cities(self, response):
        city_urls = response.xpath('//ul[@id="states-list"]/li/a/@href').extract()

        for city_url in city_urls:
            yield scrapy.Request(response.urljoin(city_url), callback=self.parse_store)

    def parse_store(self, response):
        ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)

        name = response.xpath('//div[@class="main-copy"]/h2/text()').extract_first()
        for junk in (
            (" - NOW HIRING!", ""),
            (" - Now Hiring!", ""),
            (" - NOW OPEN!", ""),
            (" - Now Open!", ""),
        ):
            name = name.replace(*junk)

        properties = {
            "ref": ref,
            "name": name,
            "addr_full": response.xpath(
                '//div[@class="location-info"]//data[@itemprop="streetAddress"]/text()'
            ).extract_first(),
            "city": response.xpath(
                '//div[@class="location-info"]//data[@itemprop="addressLocality"]/text()'
            ).extract_first(),
            "state": response.xpath(
                '//div[@class="location-info"]//data[@itemprop="addressRegion"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                '//div[@class="location-info"]//data[@itemprop="postalCode"]/text()'
            ).extract_first(),
            "country": "US",
            "lat": response.xpath(
                '//span[@class="directions"]/@data-lat'
            ).extract_first(),
            "lon": response.xpath(
                '//span[@class="directions"]/@data-lng'
            ).extract_first(),
            "phone": response.xpath(
                '//div[@class="location-info"]//data[@itemprop="telephone"]/text()'
            ).extract_first(),
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)
