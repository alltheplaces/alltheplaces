# -*- coding: utf-8 -*-
import scrapy
import re
import json

from locations.items import GeojsonPointItem


class AmcTheatresSpider(scrapy.Spider):
    name = "amctheatres"
    allowed_domains = ['amctheatres.com']
    start_urls = (
        'https://www.amctheatres.com/sitemaps/sitemap-theatres.xml',
    )

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//url/loc/text()').extract()
        for path in city_urls:
            yield scrapy.Request(
                path.strip(),
                callback=self.parse_store,
            )

    def parse_store(self, response):
        properties = {
            'name': response.xpath('/html/body/div/div/main/div/section/div/div/div/div/div/div/h1/text()').extract_first(),
            'website': response.request.url,
            'ref': response.xpath('/html/body/div/div/main/div/section/div/div/div/div/div/div/h1/text()').extract_first(),
            'addr_full': response.xpath('//*[@id="relay-data"]/text()').extract_first().split('"addressLine1":"')[1].split('"')[0],
            'city': response.xpath('//*[@id="relay-data"]/text()').extract_first().split('"city":"')[1].split('"')[0],
            'state': response.xpath('//*[@id="relay-data"]/text()').extract_first().split('"state":"')[1].split('"')[0],
            'postcode': response.xpath('//*[@id="relay-data"]/text()').extract_first().split('"postalCode":"')[1].split('"')[0],
             'lat': float(response.xpath('/html/head/meta[17][@content]').extract_first().split('content="')[1].split('"')[0]),
             'lon': float(response.xpath('/html/head/meta[18][@content]').extract_first().split('content="')[1].split('"')[0]),
        }
        
        yield GeojsonPointItem(**properties)