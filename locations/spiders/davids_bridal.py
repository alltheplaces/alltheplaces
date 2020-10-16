# -*- coding: utf-8 -*-
import re
import json

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    'Mo':0,
    'Tu':0,
    'We':0,
    'Th':0,
    'Fr':0,
    'Sa':1,
    'Su':2
}


class DavidsBridalSpider(scrapy.Spider):
    name = "davids_bridal"
    item_attributes = {'brand': 'Davids Bridal'}
    allowed_domains = ['www.davidsbridal.com']
    start_urls = [
        'https://www.davidsbridal.com/DBIStoresDirectoryView',
    ]
    download_delay = 0.3

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for day in DAY_MAPPING:
            open_close = hours[DAY_MAPPING[day]]
            if open_close.lower() in ['closed', '']:
                continue
            else:
                open_time, close_time = open_close.split(' - ') 
                opening_hours.add_range(day=day,
                                        open_time=open_time,
                                        close_time=close_time,
                                        time_format='%I:%M%p'
                                        )

        return opening_hours.as_opening_hours()
    
    def parse(self, response):
        locations = response.xpath('//div[@class="span6"]/a/@href').extract()
        for location in locations:
            yield scrapy.Request(location, callback=self.parse_store)

    def parse_store(self, response):
        # Handle closed stores
        try: 
            store_data = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').extract_first())
            
            properties = {
            'ref':  re.search(r'stLocId=([0-9]+)', response.url).group(1),
            'name': store_data['name'],
            'addr_full': store_data['address']['streetAddress'],
            'city': store_data['address']['addressLocality'],
            'state': store_data['address']['addressRegion'],
            'postcode': store_data['address']['postalCode'],
            'country': store_data['address']['addressCountry'],
            'phone': store_data['telephone'],
            'website': response.url,
            'lat': store_data['geo'].get('latitude', ''),
            'lon': store_data['geo'].get('longitude', ''),
            }

            hours = store_data.get('openingHours')
            if hours:
                properties['opening_hours'] = self.parse_hours(hours)

            yield GeojsonPointItem(**properties)

        except json.decoder.JSONDecodeError:
            pass
       