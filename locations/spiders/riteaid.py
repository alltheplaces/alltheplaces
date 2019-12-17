# -*- coding: utf-8 -*-
import scrapy
import json
import re
from locations.items import GeojsonPointItem

class RiteAidSpider(scrapy.Spider):
    name = "riteaid"
    brand = "Rite Aid"
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

    def parse(self, response):
        urls = response.xpath('//a[@class="c-directory-list-content-item-link"]/@href').extract()

        for url in urls:
            if len(url.split('/')) == 3:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_city)
            elif len(url.split('/')) == 4:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_location)
            else:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_state)

    def parse_state(self, response):
        state_urls = response.xpath('//a[@class="c-directory-list-content-item-link"]/@href').extract()

        for url in state_urls:
            if len(url.split('/')) == 5:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_location)
            else:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_city)

    def parse_city(self, response):
        city_urls = response.xpath('//a[@itemprop="url"]/@href').extract()

        for url in city_urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):
        ref = response.xpath('normalize-space(//h1[contains(@itemprop,"name")]/text())').extract_first()
        brand_elem = response.xpath('//div[@class="alert alert-danger"]/text()').extract_first()

        if brand_elem: #Changed ownership as part of the sale of select Rite Aid stores to Walgreens
            brand = 'Walgreens'
        else:
            brand = re.search(r'([^#//s*]+)', ref).group(1)

        hours_elem = response.xpath('//div[@class="Hours-store"]//div[contains(@class,"c-location-hours-details-wrapper")]/@data-days')
        if hours_elem:  # not shop, only clinic
            hours = json.loads(hours_elem.extract_first())
        else:
            hours = json.loads(response.xpath('//div[contains(@class,"c-location-hours-details-wrapper")]/@data-days').extract_first())

        properties = {
            'ref': ref,
            'addr_full': response.xpath('normalize-space(//span[contains(@itemprop,"streetAddress")]/span/text())').extract_first(),
            'state': response.xpath('normalize-space(//abbr[contains(@itemprop,"addressRegion")]/text())').extract_first(),
            'city': response.xpath('normalize-space(//span[contains(@itemprop,"addressLocality")]/text())').extract_first(),
            'postcode': response.xpath('normalize-space(//span[contains(@itemprop,"postalCode")]/text())').extract_first(),
            'country': response.xpath('normalize-space(//abbr[contains(@itemprop,"addressCountry")]/text())').extract_first(),
            'phone': response.xpath('//span[contains(@itemprop,"telephone")]/text()').extract_first(),
            'lat': float(response.xpath('//meta[contains(@itemprop,"latitude")]/@content').extract_first()),
            'lon' : float(response.xpath('//meta[contains(@itemprop,"longitude")]/@content').extract_first()),
            'website': response.url,
            'opening_hours': self.store_hours(hours),
            'extras': {
                'brand': brand.strip()
            }

        }

        yield GeojsonPointItem(**properties)