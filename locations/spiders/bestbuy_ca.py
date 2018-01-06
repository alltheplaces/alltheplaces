# -*- coding: utf-8 -*-
import scrapy
import json
import re
from datetime import date
from urllib.parse import urlparse, parse_qsl


from locations.items import GeojsonPointItem


class BestBuySpider(scrapy.Spider):
    name = "bestbuy-ca"
    allowed_domains = ["www.bestbuy.ca"]
    base_url = 'https://www.bestbuy.ca/'
    bb_url = 'https://www.bestbuy.ca/en-CA/secure/store-locator-view-all-stores.aspx'

    start_urls = (bb_url, )
    completed_requests = set()

    def store_hours(self, store_hours):
        store_days = store_hours.xpath('./div[@class="day"]/text()').extract()
        store_times = store_hours.xpath('./div[@class="hours"]/text()').extract()
        day_groups = []
        this_day_group = None

        if not len(store_times):
            store_times = ['00:00 AM - 00:00 AM' for i in range(7)]
        else:
            store_times = [' '.join(i.split(' ')[-5:]) for i in store_times]

        for i, day in enumerate(store_days):
            day_hours = store_times[i]
            if 'Closed' in day_hours:
                hours = 'Closed'
            elif 'Call store for hours' in day_hours:
                hours = day_hours
            else:
                match = re.search(r'^^(\d{1,2})[:]?(\d{1,2})? (A|P)M - (\d{1,2})[:]?(\d{1,2})? (A|P)M$', day_hours)
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
                if f_min is None:
                    f_min = 0
                if t_min is None:
                    t_min = 0

                hours = '{:02d}:00-{:02d}:00'.format(
                    f_hr,
                    t_hr,
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

    def parse_store(self, response):
        store_details = response.xpath('//div[@class="searchresults"]/div[@class="store-details"]')

        addr1 = store_details.xpath('ul[@class="litem"]/li[@class="store-address"]/text()').extract_first()
        city_state_zip = store_details.xpath('ul[@class="litem"]/li[@class="store-address-details"]/text()')\
            .extract_first().split('\r\n')
        phone_num = store_details.xpath('ul[@class="litem"]/li')
        for line in phone_num:
            if line.xpath('./span[@class="strong"]/text()').extract_first() is not None:
                phone = line.xpath('./text()').extract()[1].replace('\r\n', '').strip(' ')

        (num, street) = addr1.split(' ', 1)
        properties = {
            "phone": phone,
            "ref": response.url.split('=')[1],
            "name": store_details.xpath('h1/text()').extract_first(),
            "opening_hours": self.store_hours(store_details.xpath('ul[@class="litem store-hours"]/li')),
            # "lat": store_details['latitude'],
            # "lon": store_details['longitude'],
            "addr_full": addr1,
            "housenumber": num,
            "street": street,
            "city": city_state_zip[0].strip(' ').rstrip(','),
            "state": city_state_zip[1].strip(' ').rstrip(','),
            "postcode": city_state_zip[2].strip(' '),
            "country": 'Canada',
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        data = response.xpath('//ul[@class="storeListProvinceWrap"]//div[@class="litem"]/a/@href').extract()

        for store in data:
            yield scrapy.Request(self.base_url + store, callback=self.parse_store)
        # yield scrapy.Request(self.base_url + data[0], callback=self.parse_store)

