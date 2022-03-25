# -*- coding: utf-8 -*-
import re
import scrapy
from locations.items import GeojsonPointItem


class PonderosaSteakhouseSpider(scrapy.Spider):
    name = "ponderosa_steakhouse"
    item_attributes = {"brand": "Ponderosa Steakhouse", "brand_wikidata": "Q64038204"}
    allowed_domains = ["locations.pon-bon.com"]
    start_urls = ("https://locations.pon-bon.com/index.html",)

    def parse(self, response):
        urls = response.xpath('//a[@class="Directory-listLink"]/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_state)

    def parse_state(self, response):
        stateurls = response.xpath('//a[@class="Directory-listLink"]/@href').extract()

        for url in stateurls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_city)

    def parse_city(self, response):
        cityurls = response.xpath('//li[@class="Directory-listItem"]/a/@href').extract()

        for url in cityurls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_locations)

    def parse_locations(self, response):
        locationurls = response.xpath('//a[@class="Teaser-titleLink"]/@href').extract()

        for url in locationurls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse_store(self, response):
        ref = re.search(r".+/(.+)", response.url).group(1)

        properties = {
            "ref": ref.strip("/"),
            "name": response.xpath('//h2[@class="About-title"]/text()')
            .extract_first()
            .strip("About "),
            "addr_full": response.xpath(
                '//meta[@itemprop="streetAddress"]/@content'
            ).extract_first(),
            "city": response.xpath(
                '//meta[@itemprop="addressLocality"]/@content'
            ).extract_first(),
            "state": response.xpath(
                '//meta[@itemprop="addressRegion"]/@content'
            ).extract_first(),
            "postcode": response.xpath(
                '//meta[@itemprop="postalCode"]/@content'
            ).extract_first(),
            "country": response.xpath(
                '//meta[@itemprop="addressCountry"]/@content'
            ).extract_first(),
            "phone": response.xpath(
                '//meta[@itemprop="telephone"]/@content'
            ).extract_first(),
            "website": response.url,
            "lat": float(
                response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()
            ),
            "lon": float(
                response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()
            ),
        }

        yield GeojsonPointItem(**properties)
