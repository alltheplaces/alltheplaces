# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

US_STATES = [
  'al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'dc', 'de', 'fl',
  'ga', 'hi', 'id', 'il', 'in', 'ia', 'ks', 'ky', 'la', 'me', 
  'md', 'ma', 'mi', 'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 
  'nj', 'nm', 'ny', 'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'ri', 
  'sc', 'sd', 'tn', 'tx', 'ut', 'vt', 'va', 'wa', 'wv', 'wi', 
  'wy'
]

class StaplesSpider(scrapy.Spider):

    name = "staples"
    allowed_domains = ["stores.staples.com"]
    start_urls = (
        'https://stores.staples.com/',
    )

    def get_hours(self, day_hours):
        opening_hours = []
        for day in day_hours:
            hours = []
            for interval in day['intervals']:
                if interval['start'] < 1000:
                    interval['start'] = '0' + str(interval['start'])
                start = str(interval['start'])
                end = str(interval['end'])
                hours.append('{}:{}-{}:{}'.format(start[:2], start[2:], end[:2], end[2:]))
            current_hours = ', '.join(hours)
            opening_hours.append('{} {}'.format(day['day'][:2], current_hours))
        return "; ".join(opening_hours)

    def get_store_info(self, store):
        hours = store.xpath('//div[@class="c-location-hours-details-wrapper js-location-hours"]/@data-days').extract_first()
        opening_hours = self.get_hours(json.loads(hours)) or ''

        props = {
            'addr_full': store.xpath('normalize-space(.//span[@class="c-address-street-1"]/text())').extract_first(),
            'city': store.xpath('.//span[@class="c-address-city"]/span/text()').extract_first(),
            'state': store.xpath('.//abbr[@class="c-address-state"]/text()').extract_first(),
            'postcode': store.xpath('normalize-space(.//span[@class="c-address-postal-code"]/text())').extract_first(),
            'country': store.xpath('.//abbr[@class="c-address-country-name c-address-country-us"]/text()').extract_first(),
            'phone': store.xpath('.//span[@class="c-phone-number-span c-phone-main-number-span"]/text()').extract_first(),
            'ref': store.xpath('.//div[@class="c-address-store-code"]/text()').extract_first(),
            'website': store.url,
            'opening_hours': opening_hours,
            'lat': float(store.xpath('//div[@class="desktop"]//span[@class="coordinates"]/meta[@itemprop="latitude"]/@content').extract_first()) or '',
            'lon': float(store.xpath('//div[@class="desktop"]//span[@class="coordinates"]/meta[@itemprop="longitude"]/@content').extract_first()) or '',
        }
        return GeojsonPointItem(**props)

    def parse_store(self, store):
        city_stores = store.xpath('//div[@class="Directory-wrapper"]//article[@class="Teaser"]//a[@data-ya-track="visit_page"]/@href').extract()
        if len(city_stores) > 0:
            for city_store in city_stores:
                yield scrapy.Request(
                    store.urljoin(city_store),
                    callback=self.get_store_info
                )
        else:
            yield self.get_store_info(store)
    
    def parse_state(self, response):
        cities = response.xpath('//li[@class="c-directory-list-content-item"]/a/@href').extract()
        for city in cities:
            yield scrapy.Request(
                response.urljoin(city),
                callback=self.parse_store
            )
    
    def parse(self, response):
        states = response.xpath('//a[@class="c-directory-list-content-item-link"]/@href').extract()
        for state in states:
            callback = self.parse_state
            if state not in US_STATES:
                # states with a single store link directly to the store site
                callback = self.get_store_info
            yield scrapy.Request(
                response.urljoin(state), 
                callback=callback
            )
