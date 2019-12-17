# -*- coding: utf-8 -*-
import json
import re
import scrapy

from locations.items import GeojsonPointItem


SCRIPT_JSON = 'normalize-space(//script[@type="application/ld+json"]/text())'
PHONE = 'normalize-space(//span[@class="telephone-text bold"]//text())'


class HalloweenCity(scrapy.Spider):

    name = 'halloween-city'
    brand = "Halloween City"
    download_delay = 0.2
    allowed_domains = ('stores.halloweencity.com', )
    start_urls = (
        'http://stores.halloweencity.com/',
    )

    def parse_stores(self, response):

        app_json = json.loads(response.xpath(SCRIPT_JSON).extract_first())
        hours = app_json[0]['openingHours'].replace(' - ', '-').split()
        hours = [re.sub(r'[:]$', '', day_hour) for day_hour in hours]

        props = {
            'addr_full': app_json[0]['address']['streetAddress'],
            'phone': response.xpath(PHONE).extract_first(),
            'city': app_json[0]['address']['addressLocality'],
            'state': app_json[0]['address']['addressRegion'],
            'postcode': app_json[0]['address']['postalCode'],
            'phone': app_json[0]['address']['telephone'],
            'lat': float(app_json[0]['geo']['latitude']),
            'lon': float(app_json[0]['geo']['longitude']),
            'opening_hours': "; ".join(['{} {}'.format(x[0], x[1]) for x in zip(*[iter(hours)]*2)]),
            'ref': response.url,
            'website': response.url
        }

        return GeojsonPointItem(**props)

    def parse_city_stores(self, response):

        stores = response.xpath(
            '//div[@class="map-list-item-section map-list-item-top"]/a/@href').extract()
        for store in stores:
            yield scrapy.Request(
                response.urljoin(store),
                callback=self.parse_stores
            )

    def parse_state(self, response):

        city_urls = response.xpath(
            '//div[@class="map-list-item is-single"]/a/@href').extract()
        for path in city_urls:
            yield scrapy.Request(
                response.urljoin(path),
                callback=self.parse_city_stores
            )

    def parse(self, response):

        urls = response.xpath(
            '//div[@class="map-list-item is-single"]/a/@href').extract()
        for path in urls:
            yield scrapy.Request(
                response.urljoin(path),
                callback=self.parse_state
            )
