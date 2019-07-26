# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = [
    "Mon",
    "Tue",
    "Wed",
    "Thu",
    "Fri",
    "Sat",
    "Sun"
]

class AppleSpider(scrapy.Spider):
    name = "apple"
    allowed_domains = ["apple.com"]
    start_urls = (
        'https://www.apple.com/retail/storelist/',
    )

    def store_hours(self, hours):
        opening_hours = OpeningHours()
        for i in range(0, len(hours), 2):
            try:
                day_ranges = hours[i]
                times = hours[i+1].replace("Noon", "12:00 p.m.").replace('.', '')
                if times == 'Closed':
                    continue

                open_time, close_time = re.search(r'([\d:]+\s[apm]+)\s-\s([\d:]+\s[apm]+)', times).groups()

                for day_range in day_ranges.split(','):
                    if '-' in day_range:
                        start_day, end_day = day_range.split(' - ')

                    else:
                        start_day, end_day = day_range, day_range

                    start_day = start_day.strip(' :')
                    end_day = end_day.strip(' :')

                    for day in DAY_MAPPING[DAY_MAPPING.index(start_day):DAY_MAPPING.index(end_day)]:
                        opening_hours.add_range(day=day[:2], open_time=open_time, close_time=close_time, time_format='%I:%M %p')
            except:
                continue

        return opening_hours.as_opening_hours()

    def parse(self, response):
        countries = response.xpath('//div[contains(@id, "stores")]')
        for country in countries:
            country_code = country.xpath('./@id').extract_first()[:2].upper()

            shops = country.xpath('.//li/a/@href').extract()
            for shop in shops:
                yield scrapy.Request(response.urljoin(shop),
                                     callback=self.parse_shops,
                                     meta={"properties": {"country": country_code}})

    def parse_shops(self, response):

        properties = response.meta["properties"]

        store_details = response.xpath('//div[contains(@class,"store-details")]')

        properties.update({
            'website': response.url,
            'ref': "_".join(re.search(r'.*/(.*?)/(.*?)/', response.url).groups()),
            'name': response.xpath('//meta[@property="og:title"]/@content').extract_first(),
            'phone': store_details.xpath('.//span[contains(@class,"store-phone")]/text()').extract_first(),
            'addr_full': store_details.xpath('.//span[contains(@class,"store-street")]/text()').extract_first(),
            'city': store_details.xpath('.//span[contains(@class,"store-locality")]/text()').extract_first(),
            'state': store_details.xpath('.//span[contains(@class,"store-region")]/text()').extract_first(),
            'postcode': store_details.xpath('.//span[contains(@class,"store-postal-code")]/text()').extract_first(),
        })

        hours = self.store_hours(response.xpath('//div[contains(@class,"store-hours-row")]/div/text()').extract())
        if hours:
            properties['opening_hours'] = hours

        latlon_elem = response.xpath('//div[contains(@class,"copy-software")]/a/@href')
        if latlon_elem:
            lat, lon = re.search(r'&lat=(.+)&long=(.+)', latlon_elem.extract_first()).groups()
            properties['lat'] = float(lat)
            properties['lon'] = float(lon)

        yield GeojsonPointItem(**properties)
