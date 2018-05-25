# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

class VerizonSpider(scrapy.Spider):

    name = "verizon"
    allowed_domains = ["www.verizonwireless.com"]
    start_urls = (
        'https://www.verizonwireless.com/stores/',
    )

    # Once per city, parse stores
    def parse_city(self, city):
        city_stores = city.xpath('//div[@class="col-xs-3 cityListView products store-list-product list-view"]//address')
        city_locations = city.xpath('//script[text()[contains(.,"resultsList")]]/text()').extract_first()
        city_json = json.loads(city_locations.split('resultsList=')[-1].strip())
        if len(city_stores) > 0:
            for index, city_store in enumerate(city_stores):
                phone = city_store.xpath('.//span/text()').extract()[-1]
                city_name = city_json[index]['city']
                state = city_json[index]['state']
                zip_code = city_json[index]['zip']
                web = city_store.xpath('.//span/a/@href').extract_first()
                props = {
                    'addr_full': '{}, {}, {} {}'.format(city_json[index]['address'], city_name, state, zip_code),
                    'city': city_name,
                    'state': state,
                    'postcode': zip_code,
                    'phone': phone,
                    'ref': web,
                    'website': city.urljoin(web),
                    'name': city_store.xpath('.//span/a/text()').extract_first()
                }
                if city_json[index]['lat'] != 'null' and city_json[index]['lng'] != 'null':
                    props['lat'] = float(city_json[index]['lat'])
                    props['lon'] = float(city_json[index]['lng'])
                yield GeojsonPointItem(**props)
    
    # Once per state, gets cities.
    def parse_state(self, state):
        cities = state.xpath('//div[@id="cityStateLinks"]/ul[@id="cityList"]/li/a/@href').extract()
        for city in cities:
            yield scrapy.Request(
                state.urljoin(city),
                callback=self.parse_city
            )
    
    # Initial request, gets states.
    def parse(self, response):
        states = response.xpath('//div[@id="cityStateLinks"]//ul/li/a/@href').extract()
        for state in states:
            yield scrapy.Request(
                response.urljoin(state), 
                callback=self.parse_state
            )
