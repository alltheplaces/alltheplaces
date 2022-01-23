# -*- coding: utf-8 -*-
import json
import re

import scrapy
from scrapy.utils.gz import gunzip

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class AcademySpider(scrapy.Spider):
    name = "academy"
    item_attributes = {'brand': 'Academy Sports + Outdoors', 'brand_wikidata': 'Q4671380'}
    allowed_domains = []
    start_urls = [
        'https://www.academy.com/sitemap_store_1.xml.gz',
    ]

    def parse(self, response):
        body = gunzip(response.body)
        body = scrapy.Selector(text=body)
        body.remove_namespaces()
        urls = body.xpath('//url/loc/text()').extract()
        for path in urls:
            store_url = re.compile(r'https://www.academy.com/shop/storelocator/.+?/.+?/store-\d+')
            if re.search(store_url, path):
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store
                )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for elem in hours:
            day, open_time, close_time = re.search(r'([A-Za-z]+)\s([\d:]+)\s-\s([\d:]+)', elem).groups()
            opening_hours.add_range(day=day[:2], open_time=open_time, close_time=close_time)

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        properties = {
            'ref': re.search(r'.+/(.+?)/?(?:\.html|$)', response.url).group(1),
            'name': response.xpath('normalize-space(//h1[@itemprop="name"]//text())').extract_first(),
            'addr_full': response.xpath('normalize-space(//span[@itemprop="streetAddress"]//text())').extract_first(),
            'city': response.xpath('normalize-space(//span[@itemprop="addressLocality"]//text())').extract_first(),
            'state': response.xpath('normalize-space(//span[@itemprop="addressRegion"]//text())').extract_first(),
            'postcode': response.xpath('normalize-space(//span[@itemprop="postalCode"]//text())').extract_first(),
            'phone': response.xpath('//a[@id="storePhone"]/text()').extract_first(),
            'website': response.url,
            'lat': float(response.xpath('//input[@id="params"]/@data-lat').extract_first()),
            'lon': float(response.xpath('//input[@id="params"]/@data-lng').extract_first()),
        }
        
        properties['opening_hours'] = self.parse_hours(
            response.xpath('//*[@itemprop="openingHours"]/@datetime').extract()
        )
        
        yield GeojsonPointItem(**properties)
