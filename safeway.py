# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class SafewaySpider(scrapy.Spider):
    name = "safeway"
    allowed_domains = ['safeway.com']
    start_urls = (
        'https://local.safeway.com/sitemap.xml',
    )

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//*/*[@href]').extract()
        for path in city_urls:
            locationURL = re.compile(r'https://local.safeway.com/(safeway/|\S+)/\S+/\S+')
            if not re.search(locationURL, path):
                pass
            else:
                path = re.search(locationURL, path)[0]
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )

    def parse_store(self, response):

        properties = {
            'name': response.xpath('/html/body/main/div[2]/div/section[1]/div[2]/div[1]/h1/span/span[2]/text()').extract()'),
            'website': response.request.url,
            'ref': response.xpath('/html/body/main/div[2]/div/section[1]/div[2]/div[1]/h1/span/span[2]/text()').extract(),
            'addr_full': response.xpath('/html/body/main/div[2]/div/section[1]/div[2]/div[1]/div[1]/address/span[1]/span/text()').extract(),
            'city': response.xpath('/html/body/main/div[2]/div/section[1]/div[2]/div[1]/div[1]/address/span[2]/span[1]/text()').extract(),
            'state': response.xpath('/html/body/main/div[2]/div/section[1]/div[2]/div[1]/div[1]/address/abbr[1]/text()').extract(),
            'postcode': response.xpath('/html/body/main/div[2]/div/section[1]/div[2]/div[1]/div[1]/address/span[3]/text()').extract(),
             'lon': float(response.xpath('//*[@id="js-map-config-dir-map-desktop"]').extract()[0].split('"latitude":')[1].split(',')[0],
             'lat': float(response.xpath('//*[@id="js-map-config-dir-map-desktop"]').extract()[0].split('"longitude":')[1].split(',')[0],
        }

        yield GeojsonPointItem(**properties)