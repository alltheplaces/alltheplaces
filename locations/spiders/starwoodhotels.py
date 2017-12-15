# -*- coding: utf-8 -*-
import scrapy
#import json
#import re

from locations.items import GeojsonPointItem

class StarwoodHotelsSpider(scrapy.Spider):
    name = "starwoodhotels"
    allowed_domains = ["starwoodhotels.com","usablenet.com"]
    start_urls = (
        'https://www.starwoodhotels.com/preferredguest/directory/hotels/all/list.html?language=en_US',
    )
    custom_settings = {
        'USER_AGENT': 'AllThePlacesBot/1.0',
    }
    def parse(self, response):
        countries=response.xpath('//h5/a/@href')
        for country in countries:
            yield scrapy.Request(response.urljoin(country.extract()), callback=self.parse_country)

    def parse_country(self, response):
        cities=response.xpath('//h5/a/@href')
        for city in cities:
            yield scrapy.Request(response.urljoin(city.extract()), callback=self.parse_city)

    def parse_city(self, response):
        hotels=response.xpath('//a[@class="propertyName"]/@href')
        for hotel in hotels:
            yield scrapy.Request(response.urljoin(hotel.extract()), callback=self.parse_hotel)      

    def parse_hotel(self, response):
            props={} #some hotels don't have data because they don't opened yet
            if response.xpath('//li[@class="phone"]/span/text()'):
                props['phone'] = response.xpath('//li[@class="phone"]/span/text()').extract_first().replace('Phone:','').strip()

            if response.xpath('//li[@class="street-address"]/span/text()'):
                props['addr_full'] = response.xpath('//li[@class="street-address"]/span/text()').extract_first().strip()

            if response.xpath('//li[@class="postal-code"]/span/text()'):
                props['postcode'] = response.xpath('//li[@class="postal-code"]/span/text()').extract_first().strip()

            if response.xpath('//li[@class="city"]/span/text()'):    
                props['city'] = response.xpath('//li[@class="city"]/span/text()').extract_first().strip(),

            if response.xpath('//li[@class="region"]/span/text()'):
                props['state'] =response.xpath('//li[@class="region"]/span/text()').extract_first().strip(),

            if response.xpath('//li[@class="country-name"]/span/text()'):    
                props['country'] =response.xpath('//li[@class="country-name"]/span/text()').extract_first().strip(),

            yield GeojsonPointItem(
                **props,
                lat=float(response.xpath('//meta[@property="og:latitude"]/@content').extract_first()),
                lon=float(response.xpath('//meta[@property="og:longitude"]/@content').extract_first()),
                website=response.url,
                ref=response.xpath('//meta[@property="og:title"]/@content').extract_first(),
                #opening_hours=, hotels works 24h?
            )
