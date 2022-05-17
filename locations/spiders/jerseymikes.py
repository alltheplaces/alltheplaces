# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class JerseyMikesSpider(scrapy.Spider):
    name = "jerseymikes"
    item_attributes = {"brand": "Jersey Mike's Subs", "brand_wikidata": "Q6184897"}
    allowed_domains = ["jerseymikes.com"]
    start_urls = ("https://www.jerseymikes.com/locations/all",)

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//div[@class="content"]/ul/li/a/@href').extract()
        for path in city_urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_location)

    def parse_location(self, response):
        location_urls = response.xpath(
            '//div[@class="pure-g location-list"]/div/div/div[3]/a[3]/@href'
        ).extract()
        for path in location_urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_store)

    def parse_store(self, response):

        properties = {
            "name": response.xpath("//title/text()").extract_first().strip("\n\t"),
            "ref": response.xpath("//title/text()").extract_first().strip("\n\t"),
            "addr_full": response.xpath(
                '//span[@class="addr1"]/text()'
            ).extract_first(),
            "city": response.xpath('//strong[@class="city"]/text()').extract_first(),
            "state": response.xpath('//strong[@class="state"]/text()').extract_first(),
            "postcode": response.xpath('//span[@class="zip"]/text()').extract_first(),
            "phone": response.xpath('//a[@class="tel"]/text()').extract_first(),
            "website": response.request.url,
            "opening_hours": response.xpath(
                '//div[@class="location-hours"]/strong/text()'
            ).extract_first(),
            "lat": float(
                response.xpath(
                    '//a[@class="pure-button full-width margin-bottom"]/@href'
                )
                .extract_first()
                .split("/")[-1]
                .split(",")[0]
            ),
            "lon": float(
                response.xpath(
                    '//a[@class="pure-button full-width margin-bottom"]/@href'
                )
                .extract_first()
                .split("/")[-1]
                .split(",")[1]
            ),
        }

        yield GeojsonPointItem(**properties)
