# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class OrkinSpider(scrapy.Spider):
    name = "orkin"
    item_attributes = {"brand": "Orkin", "brand_wikidata": "Q7102943"}
    allowed_domains = ["orkin.com"]
    download_delay = 0.1
    start_urls = ("https://www.orkin.com/locations",)

    def parse(self, response):
        urls = response.xpath('//div[@class="states row"]//li/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_city)

    def parse_city(self, response):
        location_urls = response.xpath('//div[@class="row"][1]//li/a/@href').extract()

        for url in location_urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):

        properties = {
            "ref": response.xpath(
                '//section[@class="branch-data"]/@data-branch-id'
            ).extract_first(),
            "addr_full": response.xpath(
                '//span[@itemprop ="streetAddress"]/text()'
            ).extract_first(),
            "city": response.xpath(
                '//span[@itemprop ="addressLocality"]/text()'
            ).extract_first(),
            "state": response.xpath(
                '//span[@itemprop ="addressRegion"]/text()'
            ).extract_first(),
            "phone": response.xpath(
                '//span[@itemprop="telephone"]/text()'
            ).extract_first(),
            "name": response.xpath(
                '//h1[@class="locations-title"]/text()'
            ).extract_first(),
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)
