# -*- coding: utf-8 -*-
import json
import scrapy
from locations.items import GeojsonPointItem

HOURS_XPATH = 'normalize-space(//div[starts-with(@class, "hours-section ")])'


class PopeyesSpider(scrapy.Spider):

    name = "popeyes"
    allowed_domains = ["www.popeyes.com", "locations.popeyes.com"]
    download_delay = 0.2
    start_urls = (
        'https://locations.popeyes.com/',
    )

    def normalize_hours(self, hours, url):

        all_days = []
        reversed_hours = {}

        day_hours = hours.replace('Open 24 Hours', '').replace(
            'DINE-IN HOURS', '').replace('AM', '').replace('PM','').replace('-', '').split(r' ')
        day_hours = filter(None, day_hours)
        day_hours = zip(*[iter(day_hours)]*3)

        for day_hour in day_hours:
            short_day = day_hour[0].strip().title()[:2]
            to_hr = '{}:{}'.format(int(day_hour[2].split(':')[0]) + 12, day_hour[2].split(':')[1])
            epoch = '{}-{}'.format(day_hour[1].strip(), to_hr.strip())
            reversed_hours.setdefault(epoch, [])
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

        opening_hours = self.normalize_hours(
            location.xpath(HOURS_XPATH).extract_first(), location.url)
        props = {
            'addr_full': location.xpath(
                '//meta[@property="restaurant:contact_info:street_address"]/@content').extract_first(),
            'lon': float(location.xpath(
                '//meta[@property="place:location:longitude"]/@content').extract_first()),
            'lat': float(location.xpath(
                '//meta[@property="place:location:latitude"]/@content').extract_first()),
            'city': location.xpath(
                '//meta[@property="restaurant:contact_info:locality"]/@content').extract_first(),
            'postcode': location.xpath(
                '//meta[@property="restaurant:contact_info:postal_code"]/@content').extract_first(),
            'state': location.xpath(
                '//meta[@property="restaurant:contact_info:region"]/@content').extract_first(),
            'phone': location.xpath(
                '//meta[@property="restaurant:contact_info:phone_number"]/@content').extract_first(),
            'ref': location.url,
            'website': location.url,
            'opening_hours': opening_hours
        }
        return GeojsonPointItem(**props)

    def parse_city_stores(self, city):

        locations = city.xpath(
            '//a[@linktrack="Landing page"]/@href').extract()

        for location in locations:
            yield scrapy.Request(url=city.urljoin(location),
                                 callback=self.parse_location
                                 )

    def parse_state(self, state):

        cities = state.xpath(
            '//a[@linktrack="State index"]/@href').extract()
        for city in cities:
            yield scrapy.Request(url=state.urljoin(city),
                                 callback=self.parse_city_stores
                                 )

    def parse(self, response):

        states = response.xpath(
            '//a[@linktrack="State index"]/@href').extract()
        for state in states:
            yield scrapy.Request(url=response.urljoin(state),
                                 callback=self.parse_state
                                 )
