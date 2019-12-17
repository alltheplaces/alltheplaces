# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class SafewayCaSpider(scrapy.Spider):
    name = "safeway_ca"
    item_attributes = { 'brand': "Safeway" }
    allowed_domains = ["www.safeway.ca"]
    start_urls = (
        'https://www.safeway.ca/api/en/Store/get?Latitude=42.0354084&Longitude=-88.2825668&Skip=0&Max=60000',
    )

    def store_hours(self, store_hours):
        store_hours = store_hours.replace('Monday', 'Mo').replace('Tuesday', 'Tu').replace('Wednesday', 'We').replace('Thursday', 'Th').replace('Friday', 'Fr').replace('Saturday', 'Sa').replace('Sunday', 'Su')
        if 'Open 24 hours' in store_hours:
            return store_hours.replace('Open 24 hours', '00:00-24:00')
        else:
            hours = ''
            match = re.search(r'(\d{1,2sains}):(\d{2})(A|P)M - (\d{1,2}):(\d{2})(A|P)M', store_hours)
            if match:
                (f_hr, f_min, f_ampm, t_hr, t_min, t_ampm) = match.groups()
                f_hr = int(f_hr)
                if f_ampm == 'P':
                    f_hr += 12
                elif f_ampm == 'A' and f_hr == 12:
                    f_hr = 0
                t_hr = int(t_hr)
                if t_ampm == 'P':
                    t_hr += 12
                elif t_ampm == 'A' and t_hr == 12:
                    t_hr = 0
                
                hours = '{:02d}:{}-{:02d}:{}'.format(
                    f_hr,
                    f_min,
                    t_hr,
                    t_min,
                )
            return store_hours[:2] + ' ' + hours

    def parse(self, response):
        results = json.loads(response.body_as_unicode())
        for store in results['Data']:
            properties = {
                'ref': store['Number'],
                'name': store['Name'],
                'lat': store['Coordinates']['Latitude'],
                'lon': store['Coordinates']['Longitude'],
                'addr_full': store['AddressMain']['Line'],
                'city': store['AddressMain']['City'],
                'state': store['AddressMain']['Province'],
                'postcode': store['AddressMain']['PostalCode'],
                'phone': store['PhoneNumberHome']['Number'],
                'opening_hours': self.store_hours(store['OpeningHours'])
                }

            yield GeojsonPointItem(**properties)