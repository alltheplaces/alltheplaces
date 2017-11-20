# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class SuperAmericaSpider(scrapy.Spider):
    name = "superamerica"
    allowed_domains = ["superamerica.com"]
    start_urls = (
        'http://superamerica.com/wp-admin/admin-ajax.php?action=store_search&lat=45.0&lng=-90.0&max_results=500&search_radius=500&autoload=1',
    )

    def store_hours(self, store_hours):
        if not store_hours:
            return "24/7"

        day_groups = []
        this_day_group = None
        days = ('Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su')

        for day, hours in zip(days, store_hours):
            match = re.search(r'(\d{1,2}):(\d{2}) ([AP])M - (\d{1,2}):(\d{2}) ([AP])M', hours)
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

            if not this_day_group:
                this_day_group = dict(from_day=day, to_day=day, hours=hours)
            elif this_day_group['hours'] == hours:
                this_day_group['to_day'] = day
            elif this_day_group['hours'] != hours:
                day_groups.append(this_day_group)
                this_day_group = dict(from_day=day, to_day=day, hours=hours)
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
        data = json.loads(response.body_as_unicode())

        for store in data:
            yield scrapy.Request(
                response.urljoin(store['permalink']),
                callback=self.parse_store,
            )

    def parse_store(self, response):
        # Extract the JSON about the store that has lat/lon
        json_content = response.xpath('//script[@type="text/javascript"]/text()')[2].extract()
        json_content = json_content.split('var wpslMap_0 = ')[1]
        json_content = json_content.split(';\n/* ]]> */\n')[0]
        data = json.loads(json_content)
        # There should only be one store listed in this JSON
        data = data['locations'][0]

        properties = {
            'addr:full': data['address'],
            'addr:city': data['city'],
            'addr:state': data['state'],
            'addr:postcode': data['zip'],
            'name': data['store'],
            'ref': data['store'].split('#')[1],
        }

        phone_text = response.xpath('//div[@class="innerwrapper"]/h3').extract_first().split('\n')[-1]
        properties['phone'] = phone_text.rstrip('</h3>').strip()

        hours_list = response.xpath('//table[@class="wpsl-opening-hours"]/tr/td/time/text()').extract()
        opening_hours = self.store_hours(hours_list)
        if opening_hours:
            properties['opening_hours'] = opening_hours

        lon_lat = [
            float(data['lng']),
            float(data['lat']),
        ]

        yield GeojsonPointItem(
            properties=properties,
            lon_lat=lon_lat,
        )
