# -*- coding: utf-8 -*-
import scrapy
import re
import json
from scrapy.utils.gz import gunzip, is_gzipped

from locations.items import GeojsonPointItem

class ChaseSpider(scrapy.Spider):
    name = "chase"
    allowed_domains = ['chase.com']
    start_urls = (
        'https://locator.chase.com/sitemap-2.xml.gz',
    )

    def parse(self, response):

        sitemap = gunzip(response.body)
        regex = re.compile(r'https://locator.chase.com/\w+/\S+(?=</loc>)')
        city_urls = re.findall(regex, str(sitemap))

        for path in city_urls:
            yield scrapy.Request(
                path.strip(),
                callback=self.parse_store,
            )
        else:
            pass

    def parse_store(self, response):

        if response.xpath('//meta[@itemprop="openingHours"]/@content').extract():
            openingHours = str(response.xpath('//meta[@itemprop="openingHours"]/@content').extract()).replace("'",'').replace('[','').replace(']','')
        else:
            openingHours = response.xpath('//meta[@itemprop="openingHours"]/@content').extract()

        properties = {
        'name': response.xpath('//h1/span[@itemprop="name"]/text()').extract_first(),
        'ref': response.xpath('//h1/span[@itemprop="name"]/text()').extract_first(),
        'addr_full': response.xpath('//span[@itemprop="streetAddress"]/text()').extract_first(),
        'city': response.xpath('//span[@itemprop="addressLocality"]/text()').extract_first(),
        'state': response.xpath('//span[@itemprop="addressRegion"]/text()').extract_first(),
        'postcode': response.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
        'website': response.request.url,
        'opening_hours': openingHours,
        'lat': float(response.xpath('//meta[@property="place:location:latitude"]/@content').extract_first()),
        'lon': float(response.xpath('//meta[@property="place:location:longitude"]/@content').extract_first()),
        }

        yield GeojsonPointItem(**properties)