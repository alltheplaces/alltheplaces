# -*- coding: utf-8 -*-
import scrapy
import json
import re

DAYS={
    'Monday':'Mo',
    'Tuesday':'Tu',
    'Wednesday':'We',
    'Friday':'Fr',
    'Thursday':'Th',
    'Saturday':'Sa',
    'Sunday':'Su',
}
from locations.items import GeojsonPointItem
class RiteaidPizzaSpider(scrapy.Spider):
    name = "riteaid"
    allowed_domains = ["riteaid.com"]
    start_urls = (
        'https://locations.riteaid.com/',
    )

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None
        for day_info in store_hours:
            day = day_info['day'][:2].title()

            hour_intervals = []
            for interval in day_info['intervals']:
                f_time = str(interval['start']).zfill(4)
                t_time = str(interval['end']).zfill(4)
                hour_intervals.append('{}:{}-{}:{}'.format(
                    f_time[0:2],
                    f_time[2:4],
                    t_time[0:2],
                    t_time[2:4],
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

    def phone_normalize(self, phone):
        r=re.search(r'\+?(\s+)*(\d{1})?(\s|\()*(\d{3})(\s+|\))*(\d{3})(\s+|-)?(\d{2})(\s+|-)?(\d{2})',phone)
        return ('('+r.group(4)+') '+r.group(6)+'-'+r.group(8)+'-'+r.group(10)) if r else phone

    def parse(self, response): #high-level list of states
        states=response.xpath('//li[contains(@class,"c-directory-list-content-item")]/a/@href')
        for state in states:
            yield scrapy.Request(response.urljoin(state.extract()), callback=self.parse_state)

    def parse_state(self, response): #high-level list of cities
        cities=response.xpath('//li[contains(@class,"c-directory-list-content-item")]/a/@href')
        for city in cities:
            yield scrapy.Request(response.urljoin(city.extract()), callback=self.parse_city)

    def parse_city(self, response): #high-level list of states
        if response.xpath('//div[contains(@class,"location-list-wrap")]'):#list of shops or only one
            shops=response.xpath('//a[contains(@itemprop,"url")]/@href')
            for place in shops:
                yield scrapy.Request(response.urljoin(place.extract()), callback=self.parse_shop)
        else:
            return (self, self.parse_shop(response))

    def parse_shop(self, response):
        if not response.xpath('//div[@class="Hours-store"]//div[contains(@class,"c-location-hours-details-wrapper")]/@data-days').extract_first() : #not shop, only clinic
            hours=json.loads(response.xpath('//div[contains(@class,"c-location-hours-details-wrapper")]/@data-days').extract_first())
        else: 
            hours=json.loads(response.xpath('//div[@class="Hours-store"]//div[contains(@class,"c-location-hours-details-wrapper")]/@data-days').extract_first())
        yield GeojsonPointItem(
            lat=float(response.xpath('//meta[contains(@itemprop,"latitude")]/@content').extract_first()),
            lon=float(response.xpath('//meta[contains(@itemprop,"longitude")]/@content').extract_first()),
            phone=self.phone_normalize(response.xpath('//span[contains(@itemprop,"telephone")]/text()').extract_first()),
            website=response.xpath('//link[contains(@itemprop,"url")]/@href').extract_first(),
            ref=response.xpath('//h1[contains(@itemprop,"name")]/text()').extract_first(),
            opening_hours=self.store_hours(hours),
            addr_full=' '.join(response.xpath('//span[contains(@itemprop,"streetAddress")]/span/text()').extract()).strip(),
            city=response.xpath('//span[contains(@itemprop,"addressLocality")]/text()').extract_first(),
            state=response.xpath('//span[contains(@itemprop,"addressRegion")]/text()').extract_first(),
            postcode=response.xpath('//span[contains(@itemprop,"postalCode")]/text()').extract_first(),
            country=response.xpath('//span[contains(@itemprop,"addressCountry")]/text()').extract_first(),
        )
