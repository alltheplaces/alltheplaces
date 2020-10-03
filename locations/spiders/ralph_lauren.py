# -*- coding: utf-8 -*-
import scrapy
import json
import base64
from locations.items import GeojsonPointItem

class RalphLauren(scrapy.Spider):
    name = "ralph_lauren"
    allowed_domains = ["www.ralphlauren.com"]
    start_urls = (
        'https://www.ralphlauren.com/Stores-ShowCountries',
    )

    def parse(self, response):
        #gather URLs for all countries
        countries = response.xpath('//a[@class="store-directory-countrylink"]/@href').extract()

        for country in countries:
            yield scrapy.Request(response.urljoin(country),callback=self.parse_city)

    def parse_city(self, response):
        #all URLs for cities in the countries
        cities = response.xpath('//a[@class="store-directory-citylink"]/@href').extract()

        for city in cities:
            yield scrapy.Request(response.urljoin(city), callback=self.parse_stores)

    def parse_stores(self, response):
        # if a city has more than 1 store
        if len(response.xpath('//span[@class="store-listing-name"]/a/@href').extract()) > 0:
            stores = response.xpath('//span[@class="store-listing-name"]/a/@href').extract()

            for store in stores:
                yield scrapy.Request(response.urljoin(store), callback=self.parse_locations)
        else:
            stores = response.xpath('//a[@class="store-directory-citylink"]/@href').extract()

            for store in stores:
                yield scrapy.Request(response.urljoin(store), callback=self.parse_locations)

    def parse_locations(self, response):
        data = response.xpath('//div[@class="storeJSON hide"]/@data-storejson').extract_first()

        hours = response.xpath('//tr[@class="store-hourrow"]//td//text()').getall()
        opening_hours = []

        for i in hours:
            opening_hours.append(i.strip())

        if data:
            data = json.loads(data)[0]
            name = data.get("name", None)
            name = base64.b64decode(name).decode('utf-8')
            address = data.get("address1", None)
            address = base64.b64decode(address).decode('utf-8')

            properties = {
                'ref': data.get("id", None),
                'name': name,
                'lat': data.get("latitude", None),
                'lon': data.get("longitude", None),
                'phone': data.get("phone", None),
                'addr_full': address,
                'state': data.get("stateCode", None),
                'city': data.get("city", None),
                'country': data.get("countryCode", None),
                'postcode': data.get("postalCode", None),
                'opening_hours': opening_hours,
            }

            yield GeojsonPointItem(**properties)

