# -*- coding: utf-8 -*-
import scrapy
import json
import re
from scrapy.utils.url import urljoin_rfc
from scrapy.utils.response import get_base_url

from locations.items import GeojsonPointItem

class ApplebeesSpider(scrapy.Spider):
    name = "dick_blick"
    allowed_domains = ["www.dickblick.com"]
    start_urls = (
        'https://www.dickblick.com/stores/',
    )

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None
        for line in store_hours.split('m '):
            match = re.search(r'^(Su|Mo|Tu|We|Th|Fr|Sa) (\d{1,2}):(\d{2})(a|p)m-(\d{1,2}):(\d{2})(a|p)m?$', line)
            (day, f_hr, f_min, f_ampm, t_hr, t_min, t_ampm) = match.groups()

            f_hr = int(f_hr)
            if f_ampm == 'p':
                f_hr += 12
            elif f_ampm == 'a' and f_hr == 12:
                f_hr = 0
            t_hr = int(t_hr)
            if t_ampm == 'p':
                t_hr += 12
            elif t_ampm == 'a' and t_hr == 12:
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

    def address(self, address):
        if not address:
            return None

        addr_tags = {
            "addr:full": address['streetAddress'],
            "addr:city": address['addressLocality'],
            "addr:state": address['addressRegion'],
            "addr:postcode": address['postalCode'],
            "addr:country": address['addressCountry'],
        }

        return addr_tags

    def parse_store(self, response):
        contacts = response.xpath('//ul[@class="contact"]/li/span/text()').extract()

        properties = {
            'addr:full': contacts[0],
            'addr:city': contacts[1],
            'addr:state': contacts[2],
            'addr:postcode': contacts[3],
            'phone': contacts[4],
            'ref': response.url,
            'website': response.url,
        }

        day_groups = response.xpath('//ul[@class="hours"]/li[@class="storehours"]/text()').extract()

        opening_hours = []
        for day_group in day_groups:
            match = re.match(r'(.*): (\d+)-(\d+)', day_group)
            days, f_hr, t_hr = match.groups()
            f_hr = int(f_hr)
            t_hr = int(t_hr) + 12
            opening_hours.append('{} {:02d}:00-{:02d}:00'.format(days, f_hr, t_hr))

        if opening_hours:
            properties['opening_hours'] = '; '.join(opening_hours)

        yield GeojsonPointItem(
            properties=properties,
        )

    def parse_state(self, response):
        base_url = get_base_url(response)
        urls = response.xpath('//div/ul[@class="storelist"]/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(urljoin_rfc(base_url, path), callback=self.parse_store)

    def parse(self, response):
        base_url = get_base_url(response)
        urls = response.xpath('//div[@class="statechooser"]/select/option/@value').extract()
        for path in urls:
            yield scrapy.Request(urljoin_rfc(base_url, path), callback=self.parse_state)
