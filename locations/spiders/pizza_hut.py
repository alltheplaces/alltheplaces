# -*- coding: utf-8 -*-
import re
import scrapy
from locations.items import GeojsonPointItem


class PizzaHutSpider(scrapy.Spider):
    name = "pizza_hut"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    allowed_domains = ["pizzahut.com"]
    download_delay = 0.1
    start_urls = ("https://locations.pizzahut.com/",)

    def parse(self, response):
        urls = response.xpath('//li[@class="Directory-listItem"]/a/@href').extract()

        for url in urls:
            if len(url.split("/")) == 2:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_stores)
            else:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_cities)

    def parse_cities(self, response):
        urls = response.xpath('//a[@class="Directory-listLink"]/@href').extract()

        for url in urls:
            if len(url.split("/")) == 2:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_stores)
            else:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse_stores(self, response):
        urls = response.xpath(
            '//div[@class="Directory-content"]//li//a[@class="Teaser-titleLink"]/@href'
        ).extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse_store(self, response):
        ref = re.findall(r".com/(.+?)/(.+?)/(.+)", response.url)[0]
        ref = "_".join(ref)
        properties = {
            "name": response.xpath(
                '//span[@class="c-address-street-1"]/text()'
            ).extract_first(),
            "addr_full": response.xpath(
                '//span[@class="c-address-street-1"]/text()'
            ).extract_first(),
            "phone": response.xpath(
                '//span[@itemprop="telephone"]/text()'
            ).extract_first(),
            "city": response.xpath(
                '//span[@class="c-address-city"]/text()'
            ).extract_first(),
            "state": response.xpath(
                '//abbr[@class="c-address-state"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                '//span[@class="c-address-postal-code"]/text()'
            ).extract_first(),
            "ref": ref,
            "website": response.url,
            "lat": float(
                response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()
            ),
            "lon": float(
                response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()
            ),
        }

        yield GeojsonPointItem(**properties)
