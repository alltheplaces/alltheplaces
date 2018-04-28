# -*- coding: utf-8 -*-
import scrapy
import json
import re
from datetime import date


from locations.items import GeojsonPointItem


class BestBuySpider(scrapy.Spider):
    name = "bestbuy"
    allowed_domains = ["www.bestbuy.com"]
    base_url = 'https://store.bestbuy.com/'
    bb_url = 'https://www.bestbuy.com/browse-api/1.0/store-locator/raas?zipcode={}'

    zip_code = '94040'
    start_urls = (bb_url.format(zip_code), )
    completed_requests = set()

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None
        for i, line in enumerate(store_hours):
            for key, value in line.items():
                if key == 'date':
                    match = re.search(r'^(\d{1,4})-(\d{1,2})-(\d{1,2})$', value)
                    (y, m, d) = match.groups()
                    day = date(int(y), int(m), int(d)).strftime('%A')
                if key == 'open':
                    hours = value
                if key == 'close':
                    hours += '-' + value
            # Store hours has 2 weeks of data
            if i >= 7:
                break

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

        if this_day_group:
            day_groups.append(this_day_group)

        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]['hours'] in ('00:00-23:59', '00:00-00:00'):
            opening_hours = '24/7'
        else:
            for day_group in day_groups:
                if day_group['from_day'] == day_group['to_day']:
                    opening_hours += '{from_day} {hours}; '.format(**day_group)
                elif day_group['from_day'] == 'Mo' and day_group['to_day'] == 'Su':
                    opening_hours += '{hours}; '.format(**day_group)
                else:
                    opening_hours += '{from_day}-{to_day} {hours}; '.format(**day_group)
            opening_hours = opening_hours[:-2]
        return opening_hours

    def parse(self, response):
        json_str = response.body_as_unicode()
        data = json.loads(json_str)['data']['stores']

        bounding_box = {
            'min_lat': 100,
            'max_lat': -100,
            'min_lon': 300,
            'max_lon': -300,
            'min_lat_zip': None,
            'max_lat_zip': None,
            'min_lon_zip': None,
            'max_lon_zip': None,
        }

        for store in data:
            (num, street) = store['addr1'].split(' ', 1)
            properties = {
                "phone": store['phone'],
                "ref": store['id'],
                "name": store['name'],
                "opening_hours": self.store_hours(store['hours']),
                "lat": store['latitude'],
                "lon": store['longitude'],
                "addr_full": store['addr1'],
                "housenumber": num,
                "street": street,
                "city": store['city'],
                "state": store['state'],
                "postcode": store['zipCode'],
                "country": store['country'],
                "website": self.base_url + store['id'],
            }
            lat = float(store['latitude'])
            lon = float(store['longitude'])
            if lat < bounding_box['min_lat']:
                bounding_box['min_lat'] = lat
                bounding_box['min_lat_zip'] = store['zipCode']
            if lat > bounding_box['max_lat']:
                bounding_box['max_lat'] = lat
                bounding_box['max_lat_zip'] = store['zipCode']
            if lon < bounding_box['min_lon']:
                bounding_box['min_lon'] = lon
                bounding_box['min_lon_zip'] = store['zipCode']
            if lon > bounding_box['max_lon']:
                bounding_box['max_lon'] = lon
                bounding_box['max_lon_zip'] = store['zipCode']

            yield GeojsonPointItem(**properties)

        for key, value in bounding_box.items():
            if 'zip' in key and value is not None:
                if value in self.completed_requests:
                    self.logger.info("Skipping request for zipcode %s because we already did it", value)
                else:
                    self.completed_requests.add(value)
                    yield scrapy.Request(self.bb_url.format(value))
