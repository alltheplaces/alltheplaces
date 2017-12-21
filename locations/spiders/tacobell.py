# -*- coding: utf-8 -*-
import scrapy
import json
import traceback
import re
from locations.items import GeojsonPointItem

URL = 'https://prd-tac-api01.cfrprd.com/location/v1/stores?longitude=-88.6162872314453&latitude=42.4210510253906&distance=50'
HEADERS = {
           'Accept-Language': 'en-US,en;q=0.9',
           'Origin': 'https://www.tacobell.com',
           'Accept-Encoding': 'gzip, deflate, br',
           'Accept': '*/*',
           'Referer': 'https://www.tacobell.com/locations/',
           'Connection': 'keep-alive',
           'Device-Identifier': '68805ed9-8f43-41ce-5993-e6af2dfcdf31',
           'Host':'prd-tac-api01.cfrprd.com',
           'Authorization': 'bearer 2962bdbe503c11e58504005056b335f2',
           'Content-Type': 'application/json',
           }

DAY_NAMES = {
    'monday':'Mo',
    'tuesday': 'Tu',
    'wednesday': 'We',
    'thursday': 'Th',
    'friday': 'Fr',
    'saturday': 'Sa',
    'sunday': 'Su'
}


class TacobellSpider(scrapy.Spider):
    name = "tacobell"
    allowed_domains = ["www.tacobell.com"]

    def start_requests(self):
        yield scrapy.http.FormRequest(url=URL, method='GET',
                                          headers=HEADERS, callback=self.parse)

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None

        for day_info in DAY_NAMES:
            day = DAY_NAMES[day_info]
            o_match = re.match('(\d{1,2}):(\d{2})(am|pm|AM|PM)', store_hours[day_info]['openTime'])
            c_match = re.match('(\d{1,2}):(\d{2})(am|pm|AM|PM)', store_hours[day_info]['closeTime'])
            o_h, o_min, o_ampm = o_match.groups()
            c_h, c_min, c_ampm = c_match.groups()

            hours = '%02d:%02d-%02d:%02d' % (
                int(o_h) + 12 if o_ampm == 'pm' or o_ampm == 'PM' else int(o_h),
                int(o_min),
                int(c_h) + 12 if c_ampm == 'pm' or c_ampm == 'PM' else int(c_h),
                int(c_min),
            )

            if not this_day_group:
                this_day_group = {
                    'from_day': day,
                    'to_day': day,
                    'hours': hours
                }
            elif this_day_group['hours'] != hours:
                day_groups.append(this_day_group)
                this_day_group = {
                    'from_day': day,
                    'to_day': day,
                    'hours': hours
                }
            elif this_day_group['hours'] == hours:
                this_day_group['to_day'] = day

        day_groups.append(this_day_group)

        opening_hours = ""
        for day_group in day_groups:
            if day_group['from_day'] == day_group['to_day']:
                opening_hours += '{from_day} {hours}; '.format(**day_group)
            elif day_group['from_day'] == 'Su' and day_group['to_day'] == 'Sa':
                opening_hours += '{hours}; '.format(**day_group)
            else:
                opening_hours += '{from_day}-{to_day} {hours}; '.format(**day_group)
        opening_hours = opening_hours[:-2]

        return opening_hours

    def parse(self, response):
        content = json.loads(response.body_as_unicode())
        stores = content.get('data')

        for store in stores:
            props = {
                'lat': store.get('coordinates')['latitude'],
                'lon': store.get('coordinates')['longitude'],
                'ref': store.get('storeId'),
                'name': store.get('name'),
                'phone': store.get('phoneNumber'),
                'street': store.get('address')['line1'],
                'city': store.get('address')['city'],
                'state': store.get('address')['countrySubdivisionCode'],
                'postcode': store.get('address')['postalCode'],
                'opening_hours': self.store_hours(store.get('weeklyOperatingSchedule'))
            }

            yield GeojsonPointItem(**props)
