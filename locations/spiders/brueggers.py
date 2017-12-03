# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class BrueggersSpider(scrapy.Spider):
    name = "brueggers"
    allowed_domains = ["www.brueggers.com"]
    start_urls = (
        'https://www.brueggers.com/locations/',
    )

    def normalize_time(self, time_str):
        match = re.search(r'(\d{1,2}):(\d{2}) ([AP])M', time_str)
        h, m, am_pm = match.groups()

        return '%02d:%02d' % (
            int(h) + 12 if am_pm == 'P' else int(h),
            int(m),
        )

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None
        for day in ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'):
            day_open = store_hours[day + '_open']
            day_close = store_hours[day + '_close']

            if day_open is False:
                # On days that they're closed they set the value to 'false'
                continue

            day_open = self.normalize_time(day_open)
            day_close = self.normalize_time(day_close)

            hours = day_open + "-" + day_close

            day_short = day.title()[:2]

            if not this_day_group:
                this_day_group = dict(from_day=day_short, to_day=day_short, hours=hours)
            elif this_day_group['hours'] == hours:
                this_day_group['to_day'] = day_short
            elif this_day_group['hours'] != hours:
                day_groups.append(this_day_group)
                this_day_group = dict(from_day=day_short, to_day=day_short, hours=hours)
        day_groups.append(this_day_group)

        if not day_groups:
            return None

        if len(day_groups) == 1:
            opening_hours = day_groups[0]['hours']
            if opening_hours == '07:00-07:00':
                opening_hours = '24/7'
        else:
            opening_hours = ''
            for day_group in day_groups:
                if day_group['from_day'] == day_group['to_day']:
                    opening_hours += '{from_day} {hours}; '.format(**day_group)
                else:
                    opening_hours += '{from_day}-{to_day} {hours}; '.format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse(self, response):
        map_js = response.xpath('//script[@type="text/javascript"]/text()')[3].extract()
        lat_lons = re.findall(r'LatLng\(\s+(\S*),(\S*)\);', map_js)

        for lat, lon in lat_lons:
            yield scrapy.Request(
                'https://www.brueggers.com/wp-json/brueggers/v1/locations/search/?lat={}&lng={}'.format(
                    lat, lon
                ),
                callback=self.parse_lookup_results,
            )

    def parse_lookup_results(self, response):
        # There's extra JSON loading stuff before and after the JSON blob to skip around
        store_list = json.loads(response.body_as_unicode())

        for store_data in store_list:
            properties = {
                'phone': store_data['phone'],
                'website': store_data['guid'],
                'ref': store_data['location_id'],
                'name': store_data['post_title'],
                'addr_full': store_data['address'],
                'postcode': store_data['zip'],
                'state': store_data['state'],
                'city': store_data['city'],
                'lon': float(store_data['lng']),
                'lat': float(store_data['lat']),
            }

            opening_hours = self.store_hours(store_data)
            if opening_hours:
                properties['opening_hours'] = opening_hours

            yield GeojsonPointItem(**properties)
