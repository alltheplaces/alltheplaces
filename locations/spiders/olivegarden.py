# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class OliveGardenSpider(scrapy.Spider):
    name = "olivegarden"
    allowed_domains = ['olivegarden.com']
    start_urls = (
        'http://www.olivegarden.com/en-locations-sitemap.xml',
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
            'name': response.xpath('/html/body/div[3]/div/div/div/div/div/div/div[1]/h1').extract()[0].split('\n')[1].split('<br>')[0],
            'addr_full': response.xpath('//input[@id="restAddress"]').extract()[0].split('value="')[1].split('"')[0].split(',')[0],
            'city': response.xpath('//input[@id="restAddress"]').extract()[0].split('value="')[1].split('"')[0].split(',')[1],
            'state': response.xpath('//input[@id="restAddress"]').extract()[0].split('value="')[1].split('"')[0].split(',')[-2],
            'postcode': response.xpath('//input[@id="restAddress"]').extract()[0].split('value="')[1].split('"')[0].split(',')[-1],
            'website': response.xpath('//head/link[@rel="canonical"]/@href').extract_first(),
            'lon': float(response.xpath('//input[@id="restLatLong"]').extract()[0].split('value="')[1].split('"')[0].split(',')[1]),
            'lat': float(response.xpath('//input[@id="restLatLong"]').extract()[0].split('value="')[1].split('"')[0].split(',')[0]),
        }

        open('/tmp/tmp.txt','w').write(str(properties))

        yield GeojsonPointItem(**properties)