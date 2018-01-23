# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem

class MacysSpider(scrapy.Spider):
    name = 'macys'
    allowed_domains = ['macys.com']
    download_delay = 0.2
    start_urls = (
        'https://l.macys.com/',
    )

    def parse(self, response):
        states = response.xpath('//div[@class="c-directory-list"]/div/ul/li/a/@href').extract()
        for state in states:
            yield scrapy.Request(response.urljoin(state), callback=self.parse_state)

    def parse_state(self, response):
        # States with few stores have listings in this page.
        stores = response.xpath('//div[@class="c-location-grid-item"]')
        for store in stores:
          yield self.parse_info(store, response)
        # States with several stores list cities.
        cities = response.xpath('//a[@class="c-directory-list-content-item-link"]/@href').extract()
        for city in cities:
          yield scrapy.Request(response.urljoin(city), callback=self.parse_city)
    
    def parse_city(self, response):
        stores = response.xpath('//div[@class="c-location-grid-item"]')
        if len(stores) > 0:
            # Muliple stores on the page.
            for store in stores:
              yield self.parse_info(store, response)
        else:
            # Only one store on the page.
            store = response.xpath('//div[@id="location-info"]')
            address = store.xpath('./address/span/span[@class="c-address-street-1"]/text()').extract_first()
            city = store.xpath('./address/span/span[@itemprop="addressLocality"]/text()').extract_first()
            state = store.xpath('./address/abbr[@itemprop="addressRegion"]/text()').extract_first()
            postalCode = store.xpath('./address/span[@itemprop="postalCode"]/text()').extract_first().strip()
            country = store.xpath('./address/abbr[@itemprop="addressCountry"]/text()').extract_first()
            hours = ', '.join(store.xpath('./div[@class="c-location-hours"]/div/table/tbody/tr/@content').extract())
            phone = store.xpath('./div[@class="c-location-info-phone"]/span/text()').extract_first()
            prpoerties = {
                'addr_full': '%s, %s, %s %s' % (address, city, state, postalCode),
                'city': city,
                'state': state,
                'postcode': postalCode,
                'country': country,
                'ref': address,
                'lat': store.xpath('./span[@class="coordinates"]/meta[@itemprop="latitude"]/@content').extract_first(),
                'lon': store.xpath('./span[@class="coordinates"]/meta[@itemprop="longitude"]/@content').extract_first(),
                'phone': phone,
                'website': response.url,
                'opening_hours': hours,
                'extras': { 'name': response.xpath('//h1/text()').extract_first() } 
            }
            yield GeojsonPointItem(**prpoerties)
    
    def parse_info(self, store, response):
        address = store.xpath('./div/address/span/span[@class="c-address-street-1"]/text()').extract_first().strip()
        city = store.xpath('./div/address/span/span[@itemprop="addressLocality"]/text()').extract_first()
        state = store.xpath('./div/address/abbr[@itemprop="addressRegion"]/text()').extract_first()
        postalCode = store.xpath('./div/address/span[@itemprop="postalCode"]/text()').extract_first().strip()
        country = store.xpath('./div/address/abbr[@itemprop="addressCountry"]/text()').extract_first()
        hours = ', '.join(store.xpath('./div[@class="c-location-grid-item-hours-today"]/div/div/@content').extract())
        properties = {
            'addr_full': '%s, %s, %s %s' % (address, city, state, postalCode),
            'city': city,
            'state': state,
            'postcode': postalCode,
            'country': country,
            'ref': store.xpath('./div[@class="c-location-grid-item-link-wrapper"]/a[@data-ga-category="Get Directions"]/@href').extract_first().split('cid=')[-1],
            'lat': store.xpath('./div/span/meta[@itemprop="latitude"]/@content').extract_first(),
            'lon': store.xpath('./div/span/meta[@itemprop="longitude"]/@content').extract_first(),
            'phone': store.xpath('./div[@class="c-location-grid-item-phone"]/div/span/text()').extract_first(),
            'website': response.urljoin(store.xpath('./h5/a/@href').extract_first()),
            'opening_hours': hours,
            'extras': { 'name': store.xpath('./h5/a/text()').extract_first() }
        }
        return GeojsonPointItem(**properties)
