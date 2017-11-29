# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem

class NoodlesAndCompanySpider(scrapy.Spider):
    name = "noodles_and_company"
    allowed_domains = ["locations.noodles.com"]
    start_urls = (
        'https://locations.noodles.com/',
    )
    def parse(self, response):
        for state_url in response.xpath('//a[@class="c-directory-list-content-item-link"]/@href').re(r'(^[^\/]+$)'):
            yield scrapy.Request(
                response.urljoin(state_url),
                callback=self.parse_state,
            )

        for location_url in response.xpath('//a[@class="c-directory-list-content-item-link"]/@href').re(r'(^[^\/]+\/[^\/]+\/.+$)'):
            yield scrapy.Request(
                response.urljoin(location_url),
                callback=self.parse_location,
            )

    def parse_state(self, response):
        # For counties that have multiple locations, go to a county page listing, and go to each individual location from there.
        for county_url in response.xpath('//a[@class="c-directory-list-content-item-link"]/@href').re('(^[^\/]+\/[^\/]+$)'):
            yield scrapy.Request(
                response.urljoin(county_url),
                callback=self.parse_county,
            )

        # For counties that have only one location, go directly to that location page.
        for location_url in response.xpath('//a[@class="c-directory-list-content-item-link"]/@href').re('(^[^\/]+\/[^\/]+\/.+$)'):
            yield scrapy.Request(
                response.urljoin(location_url),
                callback=self.parse_location,
            )

    def parse_county(self, response):
        for location_block in response.xpath('//div[@class="c-location-grid-item"]'):
            location_url = location_block.xpath('.//a[@class="c-location-grid-item-link"]/@href').extract_first()
            yield scrapy.Request(
                response.urljoin(location_url),
                callback=self.parse_location,
            )

    def parse_location(self, response):
        properties = {
            'addr:full': response.xpath('//span[@class="c-address-street-1"]/text()').extract_first().strip(),
            'addr:city': response.xpath('//span[@itemprop="addressLocality"]/text()').extract_first(),
            'addr:state': response.xpath('//abbr[@itemprop="addressRegion"]/text()').extract_first(),
            'addr:postcode': response.xpath('//span[@itemprop="postalCode"]/text()').extract_first().strip(),
            'phone': response.xpath('//span[@itemprop="telephone"]/text()').extract_first(),
            'name': response.xpath('//span[@class="location-name-geo"]/text()').extract_first(),
            'ref': response.url,
            'website': response.url,
        }

        lon_lat = [
            float(response.xpath('//span/meta[@itemprop="longitude"]/@content').extract_first()),
            float(response.xpath('//span/meta[@itemprop="latitude"]/@content').extract_first()),
        ]

        yield GeojsonPointItem(
            properties=properties,
            lon_lat=lon_lat,
        )

