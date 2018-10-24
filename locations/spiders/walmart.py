# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class WalmartSpider(scrapy.Spider):
    name = "walmart"
    allowed_domains = ["walmart.com"]
    start_urls = (
        'https://www.walmart.com/sitemap_store_main.xml',
    )

    def store_hours(self, store_hours):
        if store_hours == 'Mo-Su':
            return u'24/7'
        elif store_hours is None:
            return None
        else:
            return store_hours

    def parse(self, response):
        response.selector.remove_namespaces()
        for u in response.xpath('//loc/text()').extract():
            if u.endswith('/details'):
                yield scrapy.Request(u.strip(), callback=self.parse_store)

    def parse_store(self, response):
        addr = response.xpath('//div[@itemprop="address"]')[0]
        yield GeojsonPointItem(
            lat=response.xpath('//meta[@itemprop="latitude"]/@content').extract_first(),
            lon=response.xpath('//meta[@itemprop="longitude"]/@content').extract_first(),
            ref=response.url.split('/')[4],
            phone=response.xpath('//meta[@itemprop="telephone"]/@content').extract_first(),
            name=response.xpath('//meta[@itemprop="name"]/@content').extract_first(),
            opening_hours=self.store_hours(response.xpath('//meta[@itemprop="openingHours"]/@content').extract_first()),
            addr_full=addr.xpath('//span[@itemprop="streetAddress"]/text()').extract_first(),
            city=addr.xpath('//span[@itemprop="locality"]/text()').extract_first(),
            state=addr.xpath('//span[@itemprop="addressRegion"]/text()').extract_first(),
            postcode=addr.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
        )
