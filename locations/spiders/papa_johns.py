# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class PapaJohnsSpider(scrapy.Spider):

    name = "papa_johns"
    allowed_domains = ["www.papajohns.com", ]

    start_urls = (
        'https://www.papajohns.com/locations/',
    )
    download_delay = 0.2

    def parse_hours(self, hours):

        reversed_hours = {}

        if not hours:
            return ''

        for day_hour in zip(*[iter(hours)]*2):
            short_day, hours = day_hour[0].title()[:2], day_hour[1]
            from_hr, to_hr = [hr.strip() for hr in hours.split('—')]

            short_frm_hr = from_hr.replace('AM', '').strip()
            if re.search('PM', to_hr):
                hour, minute = to_hr.replace('PM', '').strip().split(':')
                short_to_hr = '{}:{}'.format(str(int(hour)+12), minute)
            else:
                times = re.findall(r"([\d]+:[\d]+)",to_hr)
                if times:
                    short_to_hr = times[0]
            final_day_hour = '{}-{}'.format(short_frm_hr, short_to_hr)

            reversed_hours.setdefault(final_day_hour, [])
            reversed_hours[final_day_hour].append(short_day)

        if len(reversed_hours) == 1 and list(reversed_hours)[0] == '00:00-24:00':
            return '24/7'

        opening_hours = []

        for key, value in reversed_hours.items():
            if len(value) == 1:
                opening_hours.append('{} {}'.format(value[0], key))
            else:
                opening_hours.append(
                    '{}-{} {}'.format(value[0], value[-1], key))

        return "; ".join(opening_hours)

    def parse_store(self, response):
        hours = response.xpath('//div[@class="hours-delivery"]/p[starts-with(@class, "schedule")]//text()').extract()
        opening_hours = self.parse_hours(hours)

        props = {
            'ref': response.xpath('//p[@class="store-number"]/strong/text()').extract_first(),
            'website': response.url,
            'addr_full': response.xpath('//div[@class="streetAddress"]/text()').extract_first(),
            'phone': response.xpath('//span[@itemprop="telephone"]/a/text()').extract_first(),
            'city': response.xpath('//span[@itemprop="addressLocality"]/text()').extract_first(),
            'postcode': response.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
            'state': response.xpath('//span[@itemprop="addressRegion"]/text()').extract_first(),
            'opening_hours': opening_hours,
            'lat': float(response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()),
            'lon': float(response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()),
        }

        yield GeojsonPointItem(**props)

    def parse(self, response):
        stores = response.xpath('//h5[@class="street-address"]/a/@href').extract()

        for store in stores:
            yield scrapy.Request(
                response.urljoin(store),
                callback=self.parse_store
            )
