# -*- coding: utf-8 -*-
import json
import scrapy
from locations.items import GeojsonPointItem


class ArbysSpider(scrapy.Spider):

    name = "arby"
    allowed_domains = ["locations.arbys.com"]
    download_delay = 0.2
    start_urls = (
        'https://locations.arbys.com',
    )

    def get_hours(self, day_hours):

        normalized_hours = []
        opening_hours = []
        hours_day = {}
        for day_hour in day_hours:
            short_day = day_hour['day'].title()[:2]
            epochs = day_hour['intervals']
            hours = []

            for epoch in epochs:
                if epoch['start'] == 0 and epoch['end'] == 0:
                    hours.append('00:00-24:00')

                if len(str(epoch['start'])) == 4 and len(str(epoch['end'])) == 1:
                    start =str(epoch['start'])
                    temp_hour = '{}:{}-0{}:00'.format(start[:2], start[2:],epoch['end'])
                    hours.append(temp_hour)

                if len(str(epoch['start'])) == 4 and len(str(epoch['end'])) == 4:
                    start, end =str(epoch['start']), str(epoch['end'])
                    temp_hour = '{}:{}-{}:{}'.format(start[:2], start[2:],end[:2], end[2:])
                    hours.append(temp_hour)

                if len(str(epoch['start'])) == 3 and len(str(epoch['end'])) == 4:
                    start, end =str(epoch['start']), str(epoch['end'])
                    temp_hour = '0{}:{}-{}:{}'.format(start[:1], start[1:],end[:2], end[2:])
                    hours.append(temp_hour)

                if len(str(epoch['start'])) == 4 and len(str(epoch['end'])) == 3:
                    start, end =str(epoch['start']), str(epoch['end'])
                    temp_hour = '{}:{}-0{}:{}'.format(start[:2], start[2:],end[:1], end[1:])
                    hours.append(temp_hour)

                if len(str(epoch['start'])) == 3 and len(str(epoch['end'])) == 1:
                    start, end =str(epoch['start']), str(epoch['end'])
                    temp_hour = '0{}:{}-0{}:00'.format(start[:1],start[1:], start[2:],end)
                    hours.append(temp_hour)

            if not hours_day:
                hours_day = {
                    'from_day': short_day,
                    'to_day': short_day,
                    'hours': ",".join(hours)
                }
            elif ",".join(hours) == hours_day['hours']:
                hours_day['to_day'] = short_day
            elif ",".join(hours) != hours_day['hours']:
                normalized_hours.append(hours_day)

                hours_day = {
                    'from_day': short_day,
                    'to_day': short_day,
                    'hours': ",".join(hours)
                }
        normalized_hours.append(hours_day)

        for o_hr in normalized_hours:
            if o_hr['from_day'] == o_hr['to_day']:
                opening_hours.append('{} {}'.format(o_hr['from_day'], o_hr['hours']))
            else:
                opening_hours.append('{}-{} {}'.format(o_hr['from_day'], o_hr['to_day'],
                                                       o_hr['hours']))

        return "; ".join(opening_hours)

    def get_store_info(self, store):

        hours = store.xpath('.//span[@class="c-location-hours-today js-location-hours"]/@data-days').extract_first()
        opening_hours = self.get_hours(json.loads(hours)) or ''

        props = {
            'addr_full': store.xpath('normalize-space(.//span[@class="c-address-street-1"]/text())').extract_first(),
            'city': store.xpath('.//span[@class="c-address-city"]/span/text()').extract_first(),
            'state': store.xpath('.//abbr[@class="c-address-state"]/text()').extract_first(),
            'postcode': store.xpath('normalize-space(.//span[@class="c-address-postal-code"]/text())').extract_first(),
            'country': store.xpath('.//abbr[@class="c-address-country-name c-address-country-us"]/text()').extract_first(),
            'phone': store.xpath('.//span[@class="c-phone-number-span c-phone-main-number-span"]/text()').extract_first(),
            'ref': store.xpath('.//div[@class="logistics-detail-store-id hidden-xs hidden-sm"]/text()').extract_first(),
            'website': store.url,
            'opening_hours': opening_hours,
            'lat': float(store.xpath('.//meta[@itemprop="latitude"]/@content').extract_first()) or '',
            'lon': float(store.xpath('.//meta[@itemprop="longitude"]/@content').extract_first()) or '',
        }
        return GeojsonPointItem(**props)

    def parse_store(self, store):
        listings = store.xpath('//div[@class="row row-vertical-margin-bottom"]')
        if listings:
            city_stores = store.xpath('//a[@class="c-location-grid-item-link c-location-grid-item-link-visitpage"]/@href').extract()
            for city_store in city_stores:
                yield scrapy.Request(
                    store.urljoin(city_store),
                    callback=self.get_store_info
                )
        else:
            self.get_store_info(store)

    def parse_state(self, response):

        cities = response.xpath('//li[@class="c-directory-list-content-item"]/a/@href').extract()
        for city in cities:
            yield scrapy.Request(
                response.urljoin(city),
                callback=self.parse_store
            )

    def parse(self, response):
        states = response.xpath('//li[@class="c-directory-list-content-item"]/a/@href').extract()

        for state in states:
            yield scrapy.Request(
                response.urljoin(state),
                callback=self.parse_state
            )
