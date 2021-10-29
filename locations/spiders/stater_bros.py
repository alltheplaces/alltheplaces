# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem

class StaterBrosSpider(scrapy.Spider):
    name = 'stater_bros'
    item_attributes = { 'brand': "Stater Bros" }
    allowed_domains = ['www.staterbros.com']

    def start_requests(self):
        urls = [
            'http://www.staterbros.com/store-locator/',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        stores = response.xpath('//div[@class="store"]')
        for index, store in enumerate(stores):
          properties = {
            'addr_full': store.xpath('@data-address').extract_first(),
            'ref': index,
            'lon': store.xpath('@data-longitude').extract_first(),
            'lat': store.xpath('@data-latitude').extract_first(),
            'opening_hours': ' '.join(stores[0].xpath('div[@class="right"]/div[@class="hours"]/p/text()').extract()[:2]),
            'name': store.xpath('div[@class="left"]/div[@class="name"]/text()').extract_first()
          }

          if len(store.xpath('div[@class="left"]/div[@class="phone"]/p/text()').extract()) > 0:
            properties['phone'] = store.xpath('div[@class="left"]/div[@class="phone"]/p/text()').extract()[1]
          
          yield GeojsonPointItem(**properties)
