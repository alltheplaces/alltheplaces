# -*- coding: utf-8 -*-
import json
import re
import scrapy
from locations.items import GeojsonPointItem

HOURS_XPATH = '//span[@class="c-location-hours-today js-location-hours"]/@data-days'

class AutoZoneSpider(scrapy.Spider):

    name = "auto_zone"
    allowed_domains = ["www.autozone.com"]
    download_delay = 0.2
    start_urls = (
        'https://www.autozone.com/locations/',
    )

    def normalize_hours(self, hours):

        all_days = []
        reversed_hours = {}

        for hour in json.loads(hours):
            all_intervals = []
            short_day = hour['day'].title()[:2]
            for interval in hour['intervals']:
                start = str(interval['start'])
                end = str(interval['end'])
                from_hr = "{}:{}".format(start[:len(start)-2],
                                         start[len(start)-2:]
                                         )
                to_hr = "{}:{}".format(end[:len(end)-2],
                                       end[len(end)-2:]
                                       )
                epoch = '{}-{}'.format(from_hr, to_hr)
                all_intervals.append(epoch)
            reversed_hours.setdefault(', '.join(all_intervals), [])
            reversed_hours[epoch].append(short_day)

        if len(reversed_hours) == 1 and list(reversed_hours)[0] == '00:00-24:00':
            return '24/7'
        opening_hours = []

        for key, value in reversed_hours.items():
            if len(value) == 1:
                opening_hours.append('{} {}'.format(value[0], key))
            else:
                opening_hours.append(
                    '{}-{} {}'.format(value[0], value[-1], key))
        return "; ".join(opening_hours)

    def parse_location(self, location):

        opening_hours = self.normalize_hours(location.xpath(HOURS_XPATH).extract_first())
        props = {
            'addr_full': location.xpath(
                '//meta[@itemprop="streetAddress"]/@content').extract_first(),
            'lat': float(location.xpath(
                '//meta[@itemprop="latitude"]/@content').extract_first()),
            'lon': float(location.xpath(
                '//meta[@itemprop="longitude"]/@content').extract_first()),
            'city': location.xpath(
                '//span[@class="c-address-city"]/text()').extract_first(),
            'postcode': location.xpath(
                '//span[@class="c-address-postal-code"]/text()').extract_first(),
            'state': location.xpath(
                '//abbr[@class="c-address-state"]/text()').extract_first(),
            'phone': location.xpath(
                '//span[@class="c-phone-number-span c-phone-main-number-span"]/text()').extract_first(),
            'ref': location.url,
            'website': location.url,
            'opening_hours': opening_hours
        }
        return GeojsonPointItem(**props)

    def parse_city_stores(self, city):

        locations = city.xpath(
            '//a[@class="c-location-grid-item-link"]/@href').extract()

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
