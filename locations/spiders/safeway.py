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
            locationURL = re.compile(r'https://local.safeway.com/(safeway/|\S+)/\S+/\S+/\S+.html')
            if not re.search(locationURL, path):
                pass
            else:
                path = re.search(locationURL, path)[0].strip('"/>')
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )

    def parse_store(self, response):

        properties = {
            'name': response.xpath('/html/body/main/div[2]/div/section[1]/div[2]/div[1]/h1/span/span[2]/text()').extract_first(),
            'website': response.request.url,
            'ref': response.xpath('/html/body/main/div[2]/div/section[1]/div[2]/div[1]/h1/span/span[2]/text()').extract_first(),
            'opening_hours': " ".join(response.xpath('/html/body/main/div[2]/div/section[1]/div[2]/div[2]/div[1]/div[2]/div[@data-days]').extract_first().split("data-days=\'")[1].split("\'")[0].replace(']','').replace('{','').replace('"day"','').replace('"intervals"','').replace(':','').replace('"',' ').replace(',','').replace('[','').replace('}','').replace('end','close').replace('start','open').split()),
            'addr_full': response.xpath('/html/body/main/div[2]/div/section[1]/div[2]/div[1]/div[1]/address/span[1]/span/text()').extract_first(),
            'city': response.xpath('/html/body/main/div[2]/div/section[1]/div[2]/div[1]/div[1]/address/span[2]/span[1]/text()').extract_first(),
            'state': response.xpath('/html/body/main/div[2]/div/section[1]/div[2]/div[1]/div[1]/address/abbr[1]/text()').extract_first(),
            'postcode': response.xpath('/html/body/main/div[2]/div/section[1]/div[2]/div[1]/div[1]/address/span[3]/text()').extract_first(),
             'lon': float(response.xpath('//*[@id="js-map-config-dir-map-desktop"]').extract_first().split('"latitude":')[1].split(',')[0]),
             'lat': float(response.xpath('//*[@id="js-map-config-dir-map-desktop"]').extract_first().split('"longitude":')[1].split(',')[0]),
        }

        yield GeojsonPointItem(**properties)