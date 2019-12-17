# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class SonicDriveinSpider(scrapy.Spider):
    name = "sonic_drivein"
    chain_name = "Sonic Drive-In"
    allowed_domains = ["locations.sonicdrivein.com"]
    start_urls = [
        'https://locations.sonicdrivein.com/index.html',
    ]

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
        stores = response.xpath('//li[@class="c-directory-list-content-item"]')

        for item_elem in stores:
            count = int(item_elem.xpath('.//span[@class="c-directory-list-content-item-count"]/text()').extract_first())

            if count == 1:
                yield scrapy.Request(
                    response.urljoin(item_elem.xpath('.//a/@href').extract_first()),
                    callback=self.parse_store,
                )
            else:
                yield scrapy.Request(
                    response.urljoin(item_elem.xpath('.//a/@href').extract_first()),
                )

        if not stores:
            stores = response.xpath('//h3[@class="c-location-grid-item-title"]/a/@href').extract()
            for store in stores:
                yield scrapy.Request(
                    response.urljoin(store),
                    callback=self.parse_store,
                )

    def parse_store(self, response):
        if response.xpath('//div[@class="closed"]'):
            return

        properties = {
            'addr_full': response.xpath('//span[@itemprop="streetAddress"]/span/text()').extract_first(),
            'city': response.xpath('//span[@itemprop="addressLocality"]/text()').extract_first(),
            'state': response.xpath('//abbr[@itemprop="addressRegion"]/text()').extract_first(),
            'postcode': response.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
            'phone': response.xpath('//span[@itemprop="telephone"]/text()').extract_first(),
            'website': response.xpath('//link[@rel="canonical"]/@href').extract_first(),
            'ref': response.xpath('//link[@rel="canonical"]/@href').extract_first(),
            'lon': float(response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()),
            'lat': float(response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()),
        }

        hours = json.loads(response.xpath('//div[@class="c-location-hours-details-wrapper js-location-hours"]/@data-days').extract_first())

        opening_hours = self.store_hours(hours)
        if opening_hours:
            properties['opening_hours'] = opening_hours

        yield GeojsonPointItem(**properties)
