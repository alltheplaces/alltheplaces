# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

class FazolisSpider(scrapy.Spider):

    name = "fazolis"
    allowed_domains = ["locations.fazolis.com"]
    start_urls = (
        'https://locations.fazolis.com/',
    )

    def store_info(self, store):
        phone = store.xpath('.//span[@class="c-phone-number-span c-phone-main-number-span"]/text()').extract_first()
        city = store.xpath('.//span[@class="c-address-city"]/text()').extract_first()
        state = store.xpath('.//abbr[@class="c-address-state"]/text()').extract_first()
        zip_code = store.xpath('.//span[@class="c-address-postal-code"]/text()').extract_first()
        address = store.xpath('.//span[@class="c-address-street-1"]/text()').extract_first()
        latitude = store.xpath('.//span[@class="coordinates"]/meta[@itemprop="latitude"]/@content').extract_first()
        longitude = store.xpath('.//span[@class="coordinates"]/meta[@itemprop="longitude"]/@content').extract_first()
        hours = json.loads(store.xpath('//div[@class="location-info-col-split right-split"]//div[@class="c-location-hours-details-wrapper js-location-hours"]/@data-days').extract_first())
        props = {
            'addr_full': '{}, {}, {} {}'.format(address, city, state, zip_code),
            'city': city,
            'state': state,
            'postcode': zip_code,
            'phone': phone,
            'ref': store.url,
            'name': store.xpath('//h1[contains(@itemprop,"name")]/text()').extract_first(),
            'lat': float(latitude),
            'lon': float(longitude)
        }
        return GeojsonPointItem(**props)

    def parse_store(self, store):
        yield self.store_info(store)

    # Once per city, parse stores
    def parse_city(self, city):
        # Some times >1 store per city.
        city_stores = city.xpath('//ul[@class="c-LocationGridList"]/li//a[@class="Teaser-titleLink"]/@href').extract()
        if len(city_stores) > 0:
            for store in city_stores:
                yield scrapy.Request(
                    city.urljoin(store),
                    callback=self.parse_store
                )
        # Single store in a city means store info is in this page
        else:
            yield self.store_info(city)
    
    # Once per state, gets cities.
    def parse_state(self, state):
        cities = state.xpath('//ul[@class="c-directory-list-content"]/li/a/@href').extract()
        state_stores = state.xpath('//ul[@class="c-LocationGridList"]/li//a[@class="Teaser-titleLink"]/@href').extract()
        # Check for city listings first:
        if len(cities) > 0:
            for city in cities:
                yield scrapy.Request(
                    state.urljoin(city),
                    callback=self.parse_city
                )
        # Single city has multiple stores:
        elif len(state_stores) > 0:
            for store in state_stores:
                yield scrapy.Request(
                  state.urljoin(store),
                  callback=self.parse_store
                )
        # Single store in a state means store info is in this page:
        else:
            yield self.store_info(state)
    
    # Initial request, gets states.
    def parse(self, response):
        states = response.xpath('//ul[@class="c-directory-list-content"]/li/a/@href').extract()
        for state in states:
            yield scrapy.Request(
                response.urljoin(state), 
                callback=self.parse_state
            )
