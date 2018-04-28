# -*- coding: utf-8 -*-
import scrapy
import json
import re
import ast

from locations.items import GeojsonPointItem


class CreditUnionsSpider(scrapy.Spider):
    name = "creditunions"
    allowed_domains = ["co-opcreditunions.org"]
    url = 'http://co-opcreditunions.org'
    start_urls = (
        'http://co-opcreditunions.org/locator/search-results/?loctype=AS&zip=60008&maxradius=20&country=&Submit=Search',
    )

    def normalize_time(self, time_str):
        match = re.search(r'(.*)(am|pm| a.m| p.m)', time_str)
        h, am_pm = match.groups()
        h = h.split(':')

        return '%02d:%02d' % (
            int(h[0]) + 12 if am_pm == u' p.m' or am_pm == u'pm' else int(h[0]),
            int(h[1]) if len(h) > 1 else 0,
        )

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None
        for day_info in store_hours:
            day_info = self._clean_text(day_info)

            if day_info == '':
                continue

            day_info = day_info.split(': ')
            day = day_info[0][:2]
            intervals = day_info[1].split(" - ")

            if intervals[0].lower().find('close') > -1:
                continue

            hour_intervals = []
            start = intervals[0].split(":")
            end = intervals[1].split(":")
            hour_intervals.append('{}:{}-{}:{}'.format(
                start[0].zfill(2),
                start[1].zfill(2),
                str(int(end[0]) + 12).zfill(2),
                end[1].zfill(2),
            ))
            hours = ','.join(hour_intervals)

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
        stores_data = response.xpath('//table[contains(@class, "results-locator")]/tr')

        for store in stores_data:
            content = store.xpath('td[@class="cu-td1"]')[0].extract()
            name = re.search("<h4>(.*?)</h4>", content).group(1)
            match = re.search('<address>(.*?)<br><span></span>(.*?)<span></span>\s(.*?)<span></span>(.*?)</address>', content)

            addr_full, city_state, postcode, phone = match.groups()
            city_state = city_state.split(',')
            phone = re.search('<br>(.*)', phone).group(1) if phone != '' else ''
            open_hours_data = store.xpath('td[contains(@class, "cu-td3")]/p/text()').extract()

            yield GeojsonPointItem(
                ref=name + postcode,
                phone=phone,
                name=name,
                opening_hours=self.store_hours(open_hours_data) if len(open_hours_data) > 0 else '',
                addr_full=addr_full,
                city=city_state[0].strip(),
                state=city_state[1].strip(),
                postcode=postcode
            )
    def _clean_text(self, text):
        return re.sub("[\r\n\t]", "", text).strip()