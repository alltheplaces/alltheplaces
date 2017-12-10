# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class RubiosSpider(scrapy.Spider):
    name = "rubios"
    allowed_domains = ['rubios.com']
    start_urls = (
        'https://www.rubios.com/sitemap.xml',
    )

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//url/loc/text()').extract()
        for path in city_urls:
            regex = re.compile(r'http\S+rubios.com/store-locations/\S+/\S+/\S+')
            if not re.search(regex,path):
                pass
            else:
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )

    def parse_store(self, response):

        properties = {
            'name': response.css('.store-info').extract_first().replace('\t','').split('<span itemprop="name">')[1].split('</span>')[0],
            'ref': response.css('.store-info').extract_first().replace('\t','').split('"addressLocality">')[1].split('</span>')[0],
            'addr_full': response.css('.store-info').extract_first().replace('\t','').split('itemprop="streetAddress">')[1].split('</span>')[0],
            'city': response.css('.store-info').extract_first().replace('\t','').split('"addressLocality">')[1].split('</span>')[0],
            'state': response.css('.store-info').extract_first().replace('\t','').split('itemprop="addressRegion">')[1].split('</span>')[0],
            'postcode': response.css('.store-info').extract_first().replace('\t','').split('itemprop="postalCode">')[1].split('</span>')[0],
            'phone': response.css('.store-info').extract_first().replace('\t','').split('"tel:')[1].split('"')[0],
            'opening_hours': response.css('.store-info').extract_first().replace('\t','').split('<span class="oh-display-label" style="width: 6.6em;">')[1].split('<br></span>')[0].replace('</span><span class="oh-display-times oh-display-hours">','').strip(),
            'website': response.request.url,
            'lon': float(response.xpath('//head/script[9]').extract_first().split('"lon":')[1].split('}')[0]),
            'lat': float(response.xpath('//head/script[9]').extract_first().split('"lat":')[1].split(',')[0]),
        }

        yield GeojsonPointItem(**properties)