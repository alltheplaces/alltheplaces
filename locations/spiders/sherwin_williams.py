# -*- coding: utf-8 -*-
import scrapy
import json
import re
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

from locations.items import GeojsonPointItem


class SherwinWilliamsSpider(scrapy.Spider):
    name = "sherwin-williams"
    allowed_domains = ["www.sherwin-williams.com"]
    base_url = 'https://www.sherwin-williams.com'
    store_types = [
        'PaintStore',
        'CommercialPaintStore',
        'FinishesStore',
        'FloorCoveringStore',
        'SprayEquipmentStore',
    ]
    start_lat_longs = [
        # Geographic Center of US
        (39.121545, -98.662978),
        # # West Coast of US
        # (37.379122, -122.088782),
        # # East Coast of US
        # (40.789623, -74.385320),
        # # North Border of US
        # (48.802308, -100.494044),
        # # South Border of US
        # (29.282741, -98.539294),
    ]
    sw_urls = list()
    for s_type in store_types:
        for (lat, lon) in start_lat_longs:
            sw_urls.append('https://www.sherwin-williams.com/AjaxStoreLocatorSideBarView?langId=-1&storeId=10151'
                           '&sideBarType=LSTORES&latitude={}&longitude={}&radius=100&abbrv=us&storeType={}'
                           .format(lat, lon, s_type))
    start_urls = tuple(sw_urls)
    ll_requests = set()
    retry_requests = dict()
    NUM_RETRIES = 10

    def phone_number(self, phone):
        return '{}-{}-{}'.format(phone[0:3], phone[3:6], phone[6:10])

    def store_hours(self, response, store_id):
        store_days = response.xpath('//div[@id="store_hour_{}"]//span[@class="day"]/text()'.format(store_id)).extract()
        store_times = response.xpath('//div[@id="store_hour_{}"]//span[@class="times"]/text()'.format(store_id))\
            .extract()
        day_groups = []
        this_day_group = None
        for i, day in enumerate(store_days):
            day_hours = store_times[i].replace('\n\t', '')
            if 'Closed' in day_hours:
                hours = 'Closed'
            elif 'Call store for hours' in day_hours:
                hours = day_hours
            else:
                match = re.search(r'^(\d{1,2}):(\d{2}) (A|P)M - (\d{1,2}):(\d{2}) (A|P)M$', day_hours)
                (f_hr, f_min, f_ampm, t_hr, t_min, t_ampm) = match.groups()

                f_hr = int(f_hr)
                if f_ampm in ['p', 'P']:
                    f_hr += 12
                elif f_ampm in ['a', 'A'] and f_hr == 12:
                    f_hr = 0
                t_hr = int(t_hr)
                if t_ampm in ['p', 'P']:
                    t_hr += 12
                elif t_ampm in ['a', 'A'] and t_hr == 12:
                    t_hr = 0

                hours = '{:02d}:{}-{:02d}:{}'.format(
                    f_hr,
                    f_min,
                    t_hr,
                    t_min,
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

    def build_url(self, response, corner, radius=0):
        parse_result = urlparse(response.url)
        query_string = parse_qsl(parse_result.query)
        if radius == 0:
            (lat, lon) = corner.split(',')
        qs = list()
        for item in query_string:
            if radius == 0:
                if item[0] == 'latitude':
                    qs.append((item[0], lat))
                elif item[0] == 'longitude':
                    qs.append((item[0], lon))
                else:
                    qs.append(item)
            else:
                if item[0] == 'radius':
                    qs.append((item[0], radius))
                else:
                    qs.append(item)
        qs = urlencode(qs)
        url = urlunparse((parse_result.scheme, parse_result.netloc, parse_result.path, parse_result.params,
                          qs, parse_result.fragment))
        return url

    def extract_lat_long(self, url):
        parse_result = urlparse(url)
        query_string = parse_qsl(parse_result.query)
        for item in query_string:
            if item[0] == 'latitude':
                lat = item[1]
            if item[0] == 'longitude':
                lon = item[1]
        return tuple((lat, lon))

    def parse(self, response):
        json_str = response.xpath('//script[@id="storeResultsJSON"]/text()').extract_first()
        if json_str is None and response.text == "":
            lat_long = self.extract_lat_long(response.url)
            retries = self.retry_requests.get(lat_long, 0)
            if retries < self.NUM_RETRIES:
                retries += 1
                self.retry_requests.update({lat_long: retries})
                url = self.build_url(response, ('0', '0'), radius=retries*30)
                self.logger.debug("(lat=%s, long=%s) with URL %s has failed... retry# %d" % (lat_long[0], lat_long[1],
                                                                                             response.url, retries))
                yield scrapy.Request(url, dont_filter=True)
            else:
                self.logger.warn("(lat=%s, long=%s) has failed %d number of retries... giving up!" % (lat_long[0],
                                                                                                      lat_long[1],
                                                                                                      retries))
                self.logger.debug('Processed %d lat-long pairs' % len(self.ll_requests))
            return
        data = json.loads(json_str)['stores']

        bounding_box = {
            'min_lat': 100,
            'max_lat': -100,
            'min_lon': 300,
            'max_lon': -300,
        }

        for store in data:
            store_id = store['url'].split('storeNumber=')[1]
            store_type = store['url'].split('/')[2].replace('-', ' ').title()
            (num, street) = store['address'].split(' ', 1)
            properties = {
                "phone": self.phone_number(store['phone']),
                "ref": store['storeNumber'],
                "name": store['name'],
                "extras": "Store Type: " + store_type,
                "opening_hours": self.store_hours(response, store_id),
                "lat": store['latitude'],
                "lon": store['longitude'],
                "addr_full": store['address'],
                "housenumber": num,
                "street": street,
                "city": store['city'],
                "state": store['state'],
                "postcode": store['zipcode'],
                "website": self.base_url + store['url'],
            }

            lon_lat = [
                float(store['longitude']),
                float(store['latitude']),
            ]

            bounding_box['min_lat'] = min(bounding_box['min_lat'], lon_lat[1])
            bounding_box['max_lat'] = max(bounding_box['max_lat'], lon_lat[1])
            bounding_box['min_lon'] = min(bounding_box['min_lon'], lon_lat[0])
            bounding_box['max_lon'] = max(bounding_box['max_lon'], lon_lat[0])

            yield GeojsonPointItem(**properties)

        if len(data):
            box_corners = [
                '{},{}'.format(bounding_box['min_lat'], bounding_box['min_lon']),
                '{},{}'.format(bounding_box['max_lat'], bounding_box['min_lon']),
                '{},{}'.format(bounding_box['min_lat'], bounding_box['max_lon']),
                '{},{}'.format(bounding_box['max_lat'], bounding_box['max_lon']),
            ]

            for corner in box_corners:
                if corner in self.ll_requests:
                    self.logger.info("Skipping request for %s because we already did it", corner)
                else:
                    self.ll_requests.add(corner)
                    url = self.build_url(response, corner)
                    yield scrapy.Request(url)
        else:
            self.logger.info("No results")
