# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class TheLearningExperienceSpider(scrapy.Spider):
    name = "learning_experience"
    allowed_domains = ["thelearningexperience.com"]
    start_urls = (
        'https://thelearningexperience.com/our-centers/directory',
    )

    def parse(self, response):
        for loc_path in response.xpath('//a[@itemprop="url"]/@href'):
            yield scrapy.Request(
                response.urljoin(loc_path.extract()),
                callback=self.parse_location,
            )

    def parse_location(self, response):
        properties = {
            'name': response.xpath('//h1[@class="lp-yellow-text"]/text()').extract_first(),
            'addr:full': response.xpath('//span[@itemprop="streetAddress"]/text()').extract_first(),
            'addr:city': response.xpath('//span[@itemprop="addressLocality"]/text()').extract_first(),
            'addr:state': response.xpath('//span[@itemprop="addressRegion"]/text()').extract_first(),
            'addr:postcode': response.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
            'phone': response.xpath('//a[@itemprop="telephone"]/text()').extract_first(),
            'opening_hours': response.xpath('//tr[@itemprop="openingHours"]/@datetime').extract_first(),
            'ref': response.request.url,
            'website': response.request.url,
        }

        lon_lat = [
            float(response.xpath('//meta[@name="place:location:longitude"]/@content').extract_first()),
            float(response.xpath('//meta[@name="place:location:latitude"]/@content').extract_first()),
        ]

        yield GeojsonPointItem(
            properties=properties,
            lon_lat=lon_lat,
        )
