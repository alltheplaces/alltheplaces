# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class TMobileUSSpider(scrapy.Spider):

    name = "tmobile_us"
    allowed_domains = ["www.t-mobile.com"]

    def start_requests(self):
        url = 'https://www.t-mobile.com/srvspub/storelocsearch?prepaidStores=true&authorizedRetailers=true&coporateStores=true&start=%s&count=50&dist=6000&latcentre=45.0&lngcentre=-90.0&sortBy=Store+Type'

        for start in range(0, 6000, 50):
            yield scrapy.Request(url % start)

    def store_hours(self, store_hours):
        opening_hours = []
        for day_hours in store_hours:
            day_hours = day_hours.replace('Monday', 'Mo').replace('Tuesday', 'Tu').replace('Wednesday', 'We').replace('Thursday', 'Th').replace('Friday', 'Fr').replace('Saturday', 'Sa').replace('Sunday', 'Su')
            day_hours = day_hours.replace('Weekdays', 'Mo-Fr').replace('Weekends', 'Sa-Su').replace('Holidays', 'PH').replace('Everyday', 'Mo-Su')
            day_hours = day_hours.replace('midnight', '12 PM')

            hours = ''
            match = re.search(r'(\d{1,2}):(\d{2}) (A|P)M to (\d{1,2}):(\d{2}) (A|P)M', day_hours)
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
                day_hours = day_hours.replace(match.group(), hours)
                opening_hours.append(day_hours)
            else:
                match = re.search(r'(\d{1,2}):(\d{2}) (A|P)M-(\d{1,2}):(\d{2}) (A|P)M', day_hours)
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
                    day_hours = day_hours.replace(match.group(), hours)
                opening_hours.append(day_hours)
        return "; ".join(opening_hours)

    def parse(self, response):
        results = json.loads(response.body_as_unicode())

        base_url = 'https://www.t-mobile.com'
        for store in results['stores']:
            properties = {
                'name': store['store_name'],
                'city': store['primary_city'],
                'ref': store['locationID'],
                'lon': store['long'],
                'lat': store['lat'],
                'addr_full': store['addressline'],
                'phone': store['phone'],
                'state': store['subdivision'],
                'country': store['country_region'],
                'postcode': store['postal_code'],
            }

            if 'storeHours' in store:
                properties['opening_hours'] = self.store_hours(store['storeHours'])

            if 'rspPath' in store:
                properties['website'] = base_url + store['rspPath']

            yield GeojsonPointItem(**properties)
