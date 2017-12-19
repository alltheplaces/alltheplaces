# -*- coding: utf-8 -*-
import json
import re
import scrapy

from locations.items import GeojsonPointItem


SCRIPT_JSON = 'normalize-space(//script[@type="application/ld+json"]/text())'
PHONE = 'normalize-space(//span[@class="telephone-text bold"]//text())'


class DressBarn(scrapy.Spider):

    name = 'dressbarn'
    download_delay = 0.2
    allowed_domains = ('locations.dressbarn.com', )
    start_urls = (
        'https://locations.dressbarn.com',
    )

    def parse_stores(self, response):

        app_json = json.loads(response.xpath(SCRIPT_JSON).extract_first())
        hours = app_json[0]['openingHours'].replace(' - ', '-').split()
        hours = [re.sub(r'[:]$', '', day_hour) for day_hour in hours]

        props = {
            'addr_full': response.xpath('//meta[@name="address"]/@content').extract_first(),
            'phone': response.xpath(PHONE).extract_first(),
            'city': response.xpath('//meta[@name="city"]/@content').extract_first(),
            'state': response.xpath('//meta[@name="state"]/@content').extract_first(),
            'postcode': response.xpath('//meta[@name="zip"]/@content').extract_first(),
            'lat': float(app_json[0]['geo']['latitude']),
            'lon': float(app_json[0]['geo']['longitude']),
            'opening_hours': "; ".join(['{} {}'.format(x[0], x[1]) for x in zip(*[iter(hours)]*2)]),
            'ref': response.url,
            'website': response.url
        }

        return GeojsonPointItem(**props)

    def parse_city_stores(self, response):

        stores = response.xpath(
            '//div/a[@class="store-info flex flex-hor"]/@href').extract()
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
