# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class ChuckECheeseSpider(scrapy.Spider):
    name = "chuckecheese"
    item_attributes = { 'brand': "Chuck E Cheese" }
    allowed_domains = ['chuckecheese.com']

    def start_requests(self):
        countries = ["us", "ca", "pr", "gu"]
        base_url = "https://locations.chuckecheese.com/"

        for country in countries:
            url = base_url + country

            yield scrapy.Request(url=url, callback=self.parse_state)

    def parse_state(self, response):
        states = response.xpath('//*[@class="Directory-listLink"]/@href').extract()

        base_url = "https://locations.chuckecheese.com/"

        for state in states:
            url = base_url + state
            if len(state) > 5:
                yield scrapy.Request(url=url, callback=self.parse_store)
            else:
                yield scrapy.Request(url=url, callback=self.parse_region)

    def parse_region(self, response):
        city_count = response.xpath('//*[@class="Directory-listLink"]/@data-count').extract()
        cities = response.xpath('//*[@class="Directory-listLink"]/@href').extract()

        base_url = "https://locations.chuckecheese.com"

        for count, city in zip(city_count, cities):
            city = city[2:]
            url = base_url + city
            if count == "(1)":
                yield scrapy.Request(url=url, callback=self.parse_store)
            else:
                yield scrapy.Request(url=url, callback=self.parse_city)

    def parse_city(self, response):
        stores = response.xpath('//*[@class="Teaser-link"]/@href').extract()

        base_url = "https://locations.chuckecheese.com"

        for store in stores:
            store = store[5:]
            url = base_url + store

            yield scrapy.Request(url=url, callback=self.parse_store)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        hours = list(dict.fromkeys(hours))

        for hour in hours:
            hour = hour.split(" ")
            day = hour[0]
            open_time, close_time = hour[1].split("-")

            opening_hours.add_range(day=day, open_time=open_time, close_time=close_time, time_format='%H:%M')

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        properties = {
            'ref': "_".join(re.search(r".+/(.+?)/(.+?)/(.+?)/?(?:\.html|$)", response.url).groups()),
            'addr_full': response.xpath('//*[@class="c-address-street-1"]/text()').extract_first(),
            'city': response.xpath('//*[@itemprop="addressLocality"]/@content').extract_first(),
            'state': response.xpath('//*[@itemprop="addressRegion"]/text()').extract_first(),
            'postcode': response.xpath('//*[@itemprop="postalCode"]/text()').extract_first(),
            'country': response.xpath('//*[@itemprop="addressCountry"]/text()').extract_first(),
            'lat': response.xpath('//*[@itemprop="latitude"]/@content').extract_first(),
            'lon': response.xpath('//*[@itemprop="longitude"]/@content').extract_first(),
            'phone': response.xpath('//*[@itemprop="telephone"]/text()').extract_first(),
            'website': response.url
        }

        try:
            hours = self.parse_hours(
                response.xpath('//*[@itemprop="openingHours"]/@content').extract())

            if hours:
                properties['opening_hours'] = hours
        except:
            pass

        yield GeojsonPointItem(**properties)
