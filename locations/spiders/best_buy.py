# -*- coding: utf-8 -*-
import json
import scrapy
from locations.items import GeojsonPointItem

HOURS_XPATH = '//meta[@itemprop="openingHours"]/@content'

class BestBuySpider(scrapy.Spider):

    name = "best_buy"
    allowed_domains = ["www.bestbuy.com", "stores.bestbuy.com"]
    download_delay = 0.2
    start_urls = (
        'https://stores.bestbuy.com/',
    )

    def normalize_hours(self, hours):

        opening_hours = []
        reversed_hours = {}

        for hour in hours:
            short_day, epoch = hour.split()
            reversed_hours.setdefault(epoch, [])
            reversed_hours[epoch].append(short_day)

        if len(reversed_hours) == 1 and list(reversed_hours)[0] == '00:00-24:00':
            return '24/7'

        for key, value in reversed_hours.items():
            if len(value) == 1:
                opening_hours.append('{} {}'.format(value[0], key))
            else:
                opening_hours.append(
                    '{}-{} {}'.format(value[0], value[-1], key))
        return "; ".join(opening_hours)


    def parse_location(self, location):

        opening_hours = self.normalize_hours(location.xpath(HOURS_XPATH).extract())
        addr = location.xpath('//span[starts-with(@class, "c-address-street")]/text()').extract()
        print('The location' + location.url)
        props = {
            'addr_full': ', '.join(addr),
            'lat': float(location.xpath(
                '//meta[@itemprop="latitude"]/@content').extract_first()),
            'lon': float(location.xpath(
                '//meta[@itemprop="longitude"]/@content').extract_first()),
            'city': location.xpath(
                '//span[@itemprop="addressLocality"]/text()').extract_first(),
            'postcode': location.xpath(
                '//span[@itemprop="postalCode"]/text()').extract_first(),
            'state': location.xpath(
                '//span[@itemprop="addressRegion"]/text()').extract_first(),
            'phone': location.xpath(
                '//span[@class="c-phone-number-span c-phone-main-number-span"]/text()').extract_first(),
            'ref': location.url,
            'website': location.url,
            'opening_hours': opening_hours
        }
        return GeojsonPointItem(**props)

    def parse_city_stores(self, city):

        locations = city.xpath(
            '//a[@class="location-title-link"]/@href').extract()

        if not locations:
            yield self.parse_location(city)
        else:
            for location in locations:
                yield scrapy.Request(url=city.urljoin(location),
                                     callback=self.parse_location
                                     )

    def parse_state(self, state):

        cities = state.xpath(
            '//a[@class="c-directory-list-content-item-link"]/@href').extract()
        for city in cities:
            yield scrapy.Request(url=state.urljoin(city),
                                 callback=self.parse_city_stores
                                 )

    def parse(self, response):

        states = response.xpath(
            '//a[@class="c-directory-list-content-item-link"]/@href').extract()
        for state in states:
            yield scrapy.Request(url=response.urljoin(state),
                                 callback=self.parse_state
                                 )
