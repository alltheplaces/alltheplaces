# -*- coding: utf-8 -*-
from datetime import datetime
import json
import re
from urllib.parse import urlencode

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

SINGLE_POINT_STATES = [
    ("0,64.0685,-152.2782,AK"),
    ("1,20.6538883744,-157.8631750471,HI"),
]

HUNDRED_MILES_STATES = {"MT", "WY", "SD", "ND", "NE", "NV", "AZ", "NM", "UT", "ID"}
TWENTYFIVE_MILES_STATES = {"MD", "OH", "FL", "IL", "IA", "WI", "MN", "RI", "MA", "NH",
                           "SC", "NC", "NJ", "WA", "CA", "PA", "NY"}
ADDITONAL_CITIES = [
    "Los Angeles, CA",
    "New York, NY",
    "Boston, MA",
    "Philadelphia, PA",
    "Dallas, TX",
    "Houston, TX",
    "Seattle, WA",
    "San Francisco, CA",
    "Denver, CO",
    "Minneapolis, MN",
    "Omaha, NE",
    "St. Louis, MO",
    "Chicago, IL",
    "Montgomery, AL",
    "Orlando, FL",
    "St. Petersburg, FL",
    "Atlanta, GA",
    "Poughkeepsie, NY",
    "Hartford, CT",
    "Concord, NH"
]


class YmcaSpider(scrapy.Spider):
    name = "ymca"
    brand = "YMCA"
    allowed_domains = ["ymca.net"]
    download_delay = 0.5

    def start_requests(self):
        url = 'https://www.ymca.net/find-your-y/?'

        for point in SINGLE_POINT_STATES:
            _, lat, lon, state = point.strip().split(',')
            params = {"address": "{},{}".format(lat, lon)}
            yield scrapy.Request(url=url + urlencode(params))

        with open('./locations/searchable_points/us_centroids_100mile_radius_state.csv') as points:
            next(points)
            for point in points:
                _, lat, lon, state = point.strip().split(',')
                if state in HUNDRED_MILES_STATES:
                    params = {"address": "{},{}".format(lat, lon)}
                    yield scrapy.Request(url=url + urlencode(params))

        with open('./locations/searchable_points/us_centroids_25mile_radius_state.csv') as points:
            next(points)
            for point in points:
                _, lat, lon, state = point.strip().split(',')
                if state in TWENTYFIVE_MILES_STATES:
                    params = {"address": "{},{}".format(lat, lon)}
                    yield scrapy.Request(url=url + urlencode(params))

        with open('./locations/searchable_points/us_centroids_50mile_radius_state.csv') as points:
            next(points)
            for point in points:
                _, lat, lon, state = point.strip().split(',')
                if state not in HUNDRED_MILES_STATES.union(TWENTYFIVE_MILES_STATES).union({"AK", "HI"}):
                    params = {"address": "{},{}".format(lat, lon)}
                    yield scrapy.Request(url=url + urlencode(params))

        for city in ADDITONAL_CITIES:
            params = {"address": city}
            yield scrapy.Request(url=url + urlencode(params))

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            hour = hour.strip()
            if hour == "Hours of Operation:":
                continue

            try:
                day, open_time, close_time = re.search(r'(.*?):\s(.*?)\s-\s(.*?)$', hour).groups()
            except AttributeError:  # closed
                continue
            open_time = open_time.replace('.', '')
            close_time = close_time.replace('.', '')

            open_time = (datetime.strptime(open_time, '%I:%M %p')
                         if ":" in open_time
                         else datetime.strptime(open_time, '%I %p')).strftime('%H:%M')
            close_time = (datetime.strptime(close_time, '%I:%M %p')
                          if ":" in close_time
                          else datetime.strptime(close_time, '%I %p')).strftime('%H:%M')

            opening_hours.add_range(day=day[:2],
                                    open_time=open_time,
                                    close_time=close_time,
                                    time_format='%H:%M')
        return opening_hours.as_opening_hours()

    def parse_location(self, response):
        p = response.xpath('//main//p[1]/text()').extract()
        p = [x.strip() for x in p if x.strip()]

        phone = p.pop(-1)  # last line is phone number
        city, state, postcode = re.search(r'(.*?), ([A-Z]{2}) ([\d-]+)$', p.pop(-1)).groups()  # next to last line is city/state/zip
        address = " ".join(p)  # every thing left is street address

        properties = {
            'ref': re.search(r'.+/?id=(.+)', response.url).group(1),
            'name': response.xpath('//main//h1/text()').extract_first(),
            'addr_full': address,
            'city': city,
            'state': state,
            'postcode': postcode,
            'country': 'US',
            'lat': float(response.xpath('//div[@id="y-profile-position"]/@data-latitude').extract_first()),
            'lon': float(response.xpath('//div[@id="y-profile-position"]/@data-longitude').extract_first()),
            'phone': phone.replace("Phone: ", ""),
            'website': response.xpath('//div[@id="y-profile-position"]/@data-url').extract_first()
        }
        
        properties['opening_hours'] = self.parse_hours(response.xpath('//main//p[contains(text(), "Hours")]/text()').extract())
        
        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath('//main//ul[not(contains(@class, "ymca-pagination"))]/li/h3//a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)
