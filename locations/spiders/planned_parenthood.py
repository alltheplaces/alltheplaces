# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class PlannedParenthoodSpider(scrapy.Spider):
    name = "planned_parenthood"
    allowed_domains = ["www.plannedparenthood.org"]
    start_urls = (
        'https://www.plannedparenthood.org/health-center',
    )

    def parse(self, response):
        state_urls = response.xpath('//ul[@class="quicklist-list"]/li/a/@href').extract()
        for path in state_urls:
            yield scrapy.Request(
                response.urljoin(path),
                callback=self.parse_state,
            )

    def parse_state(self, response):
        venue_urls = response.xpath('//ul[@class="quicklist-list"]/li/p/a/@href').extract()
        for path in venue_urls:
            yield scrapy.Request(
                response.urljoin(path),
                callback=self.parse_venue,
            )

    def parse_venue(self, response):
        properties = {
            'addr:full': response.xpath('//*[@itemprop="streetAddress"]/text()')[0].extract(),
            'addr:city': response.xpath('//*[@itemprop="addressLocality"]/text()')[0].extract(),
            'addr:state': response.xpath('//*[@itemprop="addressRegion"]/text()')[0].extract(),
            'addr:postcode': response.xpath('//*[@itemprop="postalCode"]/text()')[0].extract(),
            'ref': response.url,
            'website': response.url,
        }

        map_image_url = response.xpath('//img[@class="address-map"]/@src')[0].extract()
        match = re.search(r"center=(.*?),(.*?)&zoom", map_image_url)
        lon_lat = [
            float(match.group(2)),
            float(match.group(1)),
        ]

        yield GeojsonPointItem(
            properties=properties,
            lon_lat=lon_lat,
        )
