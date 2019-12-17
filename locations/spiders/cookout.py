# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class CookoutSpider(scrapy.Spider):
    name = "cookout"
    chain_name = "Cookout"
    allowed_domains = ["www.cookout.com"]
    start_urls = (
        'http://www.cookout.com/wp-admin/admin-ajax.php?action=store_search&lat=36.072635&lng=-79.79197499999998&max_results=500&radius=500',
    )

    def store_hours(self, store_hours):
        m = re.findall(
            '<tr><td>(\w*)<\/td><td><time>([0-9: APM-]*)</time></td></tr>',
            store_hours
        )

        day_groups = []
        this_day_group = dict()
        for day, hours_together in m:
            day = day[:2]
            h = re.findall(
                '([0-9]{1,2}):([0-9]{1,2}) ([APM]{2})',
                hours_together
            )
            (from_h, from_m, from_ap), (to_h, to_m, to_ap) = h

            from_h = int(from_h)
            if from_ap == 'PM':
                from_h += 12

            to_h = int(to_h)
            if to_h == 'PM':
                to_h += 12

            hours = '{:02}:{}-{:02}:{}'.format(
                from_h,
                from_m,
                to_h,
                to_m,
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
        if len(day_groups) == 1 and day_groups[0]['hours'] in ('00:00-23:59', '00:00-00:00'):
            opening_hours = '24/7'
        else:
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
        data = json.loads(response.body_as_unicode())

        for store in data:
            properties = {
                "ref": store['id'],
                "name": store['store'],
                "opening_hours": self.store_hours(store['hours']),
                "website": store['url'],
                "addr_full": store.get('address'),
                "city": store.get('city'),
                "state": store.get('state'),
                "postcode": store.get('zip'),
                "country": store.get('country'),
                "lon": float(store['lng']),
                "lat": float(store['lat']),
            }

            phone = store['phone']
            if phone:
                properties['phone'] = phone

            yield GeojsonPointItem(**properties)

        else:
            self.logger.info("No results")
