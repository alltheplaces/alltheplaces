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
        regex = re.compile(r'http\S+rubios.com/store-locations/\S+/\S+/\S+')
        for path in city_urls:
            if re.search(regex,path):
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )
            else:
                pass

    def parse_store(self, response):

        properties = {
        'name': response.xpath('//span[@itemprop="name"]/text()').extract_first(),
        'ref': response.xpath('//span[@itemprop="name"]/text()').extract_first(),
        'addr_full': response.xpath('//span[@itemprop="streetAddress"]/text()').extract_first(),
        'city': response.xpath('//span[@itemprop="addressLocality"]/text()').extract_first(),
        'state': response.xpath('//span[@itemprop="addressRegion"]/text()').extract_first(),
        'postcode': response.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
        'phone': response.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
        'website': response.request.url,
        # 'opening_hours': response.css('.store-info').extract_first().replace('\t', '').split('<span class="oh-display-label" style="width: 6.6em;">')[1].split('<br></span>')[0].replace('</span><span class="oh-display-times oh-display-hours">', '').strip(),
        'lon': float(response.xpath('//head/script[9]').extract_first().split('"lon":')[1].split('}')[0]),
        'lat': float(response.xpath('//head/script[9]').extract_first().split('"lat":')[1].split(',')[0]),
        }




        yield GeojsonPointItem(**properties)