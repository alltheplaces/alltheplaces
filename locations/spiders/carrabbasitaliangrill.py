# -*- coding: utf-8 -*-
import scrapy
import re
import json

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class CarrabbasItalianGrillSpider(scrapy.Spider):
    download_delay = 0.2
    name = "carrabbasitaliangrill"
    allowed_domains = ["carrabbas.com"]
    start_urls = (
        'https://locations.carrabbas.com/index.html',
    )

    def parse(self, response):
        stateurls = response.xpath('//div[@class="Directory-content"]//a/@href').extract()
        for url in stateurls:
            state = url.split('/')[0]
            yield scrapy.Request(response.urljoin(state), callback=self.parse_state)

    def parse_state(self, response):
        cityurls = response.xpath('//li[@class="Directory-listItem"]//a/@href').extract()
        for url in cityurls:
            city = url.split('/')[0]+"/"+url.split('/')[1]
            yield scrapy.Request(response.urljoin(city), callback=self.parse_store)

    def parse_store(self, response):
        print(response.url)
        storeurls = response.xpath('//ul[@class="Directory-listTeasers Directory-row"]//a/@href').extract()
        storeurlsing = response.xpath('//li[@class="Directory-listTeaser Directory-listTeaser--single"]//a/@href').extract()
        if len(storeurls) > 1:
            for stores in storeurls:
                print(stores)
                if stores.startswith('..'):
                    store = stores.split('..')[1]
                    print(store)
                    yield scrapy.Request(response.urljoin(store), callback=self.parse_loc)
        if len(storeurlsing) > 1git status:
            for stores in storeurlsing:
                print(stores)
                if stores.startswith('..'):
                    store = stores.split('..')[1]
                    print(store)
                    yield scrapy.Request(response.urljoin(store), callback=self.parse_loc)

    def parse_loc(self, response):
        print(response.url)
        lat = response.xpath('//meta[@itemprop="latitude"]').extract_first()
        lon = response.xpath('//meta[@itemprop="longitude"]').extract_first()
        properties = {
            'ref':  response.url,
            'name': "Carrabba's Italian Grill",
            'addr_full': response.xpath('//span[@class="c-address-street-1"]/text()').extract_first(),
            'city': response.xpath('//span[@class="c-address-city"]/text()').extract_first(),
            'state': response.xpath('//abbr[@class="c-address-state"]/text()').extract_first(),
            'postcode': response.xpath('//span[@class="c-address-postal-code"]/text()').extract_first(),
            'country': response.xpath('//abbr[@class="c-address-country-name c-address-country-us"]/text()').extract_first(),
            'lat': lat.split('content="')[1].replace('">',''),
            'lon': lon.split('content="')[1].replace('">','')
        }

        yield GeojsonPointItem(**properties)



