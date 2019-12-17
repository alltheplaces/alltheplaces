# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

NUMBER_DAY = {
    '1': 'Mo',
    '2': 'Tu',
    '3': 'We',
    '4': 'Th',
    '5': 'Fr',
    '6': 'Sa',
    '7': 'Su'
}


class CaribouCoffeeSpider(scrapy.Spider):

    name = "caribou_coffee"
    chain_name = "Caribou Coffee"
    allowed_domains = ["momentfeed-prod.apigee.net", ]

    start_urls = (
        'https://momentfeed-prod.apigee.net/api/llp.json?auth_token=CVTQBSJXYGFVUDEY&sitemap=true',
    )
    download_delay = 0.2

    def normalize_hours(self, hours):

        reversed_hours = {}
        if not hours:
            return ''
        else:
            days = [day for day in hours.split(';') if day]
            for day in days:
                day, from_hr, to_hr = day.split(',')

                short_day = NUMBER_DAY[day]
                from_hour = '{}:{}'.format(from_hr[:2], from_hr[2:])
                to_hour = '{}:{}'.format(to_hr[:2], to_hr[2:])
                epoch = '{}-{}'.format(from_hour, to_hour)

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

            return ";".join(opening_hours)

    def parse(self, response):

        stores = json.loads(response.body_as_unicode())

        for store in stores:
            opening_hours = ''
            if store.get('store_info', '').get('store_hours', ''):
                opening_hours = self.normalize_hours(
                    store['store_info']['store_hours'])

            props = {
                'ref': store['store_info']['corporate_id'],
                'addr_full': store['store_info']['address'],
                'postcode': store['store_info']['postcode'],
                'state': store['store_info']['region'],
                'website': store['store_info']['website'],
                'city': store['store_info']['locality'],
                'phone': store['store_info']['phone'],
                'lat': store['store_info']['latitude'],
                'lon': store['store_info']['longitude'],
                'opening_hours': opening_hours
            }

            yield GeojsonPointItem(**props)
