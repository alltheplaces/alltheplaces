# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem


class ErbertandGerbertsSpider(scrapy.Spider):
    name = "erbertandgerberts"
    allowed_domains = ['erbertandgerberts.com']
    start_urls = (
        'https://www.erbertandgerberts.com/store-sitemap.xml',
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
        'name': response.xpath('//h1[@class="ph__title text-cursive mb0"]/text()').extract_first(),
        'ref': response.xpath('//h1[@class="ph__title text-cursive mb0"]/text()').extract_first(),
        'addr_full': response.xpath('//address[@class]/text()').extract_first(),
        'city': response.xpath('//address[@class]/text()').extract()[1].split(',')[0],
        'state': response.xpath('//address[@class]/text()').extract()[1].split()[-2],
        'postcode': response.xpath('//address[@class]/text()').extract()[1].split()[-1],
        'phone': response.xpath('//div[@class="store__contact text-gray std-mb"]/p/a/text()').extract_first(),
        'website': response.request.url,
        'lat': float(response.xpath('//script[@type="text/javascript"]').extract()[6].split('lat         = "')[1].split('"')[0]),
        'lon': float(response.xpath('//script[@type="text/javascript"]').extract()[6].split('lng          = "')[1].split('"')[0]),
        }

        yield GeojsonPointItem(**properties)