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

    def address(self, address):
        if not address:
            return None

        addr_tags = {
            "addr_full": address[0].split('value="')[1].split('"')[0].split(',')[0],
            "city": address[0].split('value="')[1].split('"')[0].split(',')[1],
            "state": address[0].split('value="')[1].split('"')[0].split(',')[-2],
            "postcode": address[0].split('value="')[1].split('"')[0].split(',')[-1],
        }

        return addr_tags


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
            'website': response.xpath('//head/link[@rel="canonical"]/@href').extract_first(),
            'ref': " ".join(response.xpath('/html/head/title/text()').extract()[0].split('|')[0].split()),
            'lon': float(response.xpath('//input[@id="restLatLong"]').extract()[0].split('value="')[1].split('"')[0].split(',')[1]),
            'lat': float(response.xpath('//input[@id="restLatLong"]').extract()[0].split('value="')[1].split('"')[0].split(',')[0]),
        }

        address = self.address(response.xpath('//input[@id="restAddress"]').extract())
        if address:
            properties.update(address)

        yield GeojsonPointItem(**properties)