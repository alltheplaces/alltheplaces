# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class SprintSpider(scrapy.Spider):
    name = "sprint"
    allowed_domains = ["sprint.com"]
    start_urls = (
        'https://www.sprint.com/locations/',
    )

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None
        for line in store_hours:
            day = line['day'][0].upper()+line['day'][1].lower()

            if not line['intervals']:
                continue

            for period in line['intervals']:
                hours = '{0}:{1}-{2}:{3}'.format(
                    str(period['start'])[:2],
                    str(period['start'])[2:],
                    str(period['end'])[:2],
                    str(period['end'])[2:],
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

    def parse(self, response):
        states = response.xpath('//li[@class="c-directory-list-content-item"]/a[@class="c-directory-list-content-item-link"]/@href')
        for path in states:
            yield scrapy.Request(response.urljoin(path.extract()), callback=self.parse_city)


    def parse_city(self, response):
        cities = response.xpath('//li[@class="c-directory-list-content-item"]/a[@class="c-directory-list-content-item-link"]/@href')
        for path in cities:
            yield scrapy.Request(response.urljoin(path.extract()), callback=self.parse_store)

    def parse_store(self, response):
        address=response.xpath('//div[@class="LocationInfo-contact"]/address/span[@class="c-address-street"]/span/text()')
        hours=json.loads(response.xpath('//div[@id="c-hours-collapse"]/div[@class="c-location-hours"]/div[contains(@class,"c-location-hours-details-wrapper")]/@data-days').extract_first())
        yield GeojsonPointItem(
            lat=float(response.xpath('//span[@itemprop="geo"]/meta[@itemprop="latitude"]/@content').extract_first()),
            lon=float(response.xpath('//span[@itemprop="geo"]/meta[@itemprop="longitude"]/@content').extract_first()),
            phone=response.xpath('//div[@class="LocationInfo-contact"]/div[contains(@class, "c-phone-main")]/div[contains(@class,"c-phone-main-number-wrapper")]/div[@class="c-phone-number c-phone-main-number"]/span/text()').extract_first(),
            website=response.xpath('//link[@rel="canonical"]/@href').extract_first(),
            ref=response.xpath("//script[contains(., 'storeIdNumber')]/text()").re(r'storeIdNumber = \'(.*)\';')[0],
            opening_hours=self.store_hours(hours),
            addr_full=" ".join(list(map(lambda x:x.extract(),address))),
            city=response.xpath('//span[@itemprop="addressLocality"]/text()').extract_first(),
            state=response.xpath('//abbr[@itemprop="addressRegion"]/text()').extract_first(),
            postcode=response.xpath('//div[@class="LocationInfo-contact"]/address/span[@class="c-address-postal-code "]/text()').extract_first().strip(),
            country=response.xpath('//abbr[@itemprop="addressCountry"]/text()').extract_first(),
        )
