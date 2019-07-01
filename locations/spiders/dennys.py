# -*- coding: utf-8 -*-
import scrapy
import datetime
import re
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = {
    'Monday': 'Mo',
    'Tuesday': 'Tu',
    'Wednesday': 'We',
    'Thursday': 'Th',
    'Friday': 'Fr',
    'Saturday': 'Sa',
    'Sunday': 'Su'
}

class DennysSpider(scrapy.Spider):
    name = "dennys"
    allowed_domains = ["locations.dennys.com"]
    start_urls = (
        'https://locations.dennys.com/',
    )

    # def store_hours(self, store_hours):
    #     day_groups = []
    #     this_day_group = None
    #     for day_info in store_hours:
    #         day = day_info['day'][:2].title()
    #
    #         hour_intervals = []
    #         for interval in day_info['intervals']:
    #             f_time = str(interval['start']).zfill(4)
    #             t_time = str(interval['end']).zfill(4)
    #             hour_intervals.append('{}:{}-{}:{}'.format(
    #                 f_time[0:2],
    #                 f_time[2:4],
    #                 t_time[0:2],
    #                 t_time[2:4],
    #             ))
    #         hours = ','.join(hour_intervals)
    #
    #         if not this_day_group:
    #             this_day_group = {
    #                 'from_day': day,
    #                 'to_day': day,
    #                 'hours': hours
    #             }
    #         elif this_day_group['hours'] != hours:
    #             day_groups.append(this_day_group)
    #             this_day_group = {
    #                 'from_day': day,
    #                 'to_day': day,
    #                 'hours': hours
    #             }
    #         elif this_day_group['hours'] == hours:
    #             this_day_group['to_day'] = day
    #
    #     day_groups.append(this_day_group)
    #
    #     opening_hours = ""
    #     if len(day_groups) == 1 and day_groups[0]['hours'] in ('00:00-23:59', '00:00-00:00'):
    #         opening_hours = '24/7'
    #     else:
    #         for day_group in day_groups:
    #             if day_group['from_day'] == day_group['to_day']:
    #                 opening_hours += '{from_day} {hours}; '.format(**day_group)
    #             elif day_group['from_day'] == 'Su' and day_group['to_day'] == 'Sa':
    #                 opening_hours += '{hours}; '.format(**day_group)
    #             else:
    #                 opening_hours += '{from_day}-{to_day} {hours}; '.format(**day_group)
    #         opening_hours = opening_hours[:-2]
    #
    #     return opening_hours

    def parse_hours(self, elements):
        opening_hours = OpeningHours()

        for elem in elements:
            day = elem.xpath('.//td[@class="c-hours-details-row-day"]/text()').extract_first()
            intervals = elem.xpath('.//td[@class="c-hours-details-row-intervals"]')

            if intervals.xpath('./text()').extract_first() == "Closed":
                continue
            if intervals.xpath('./span/text()').extract_first() == "Open 24 hours":
                opening_hours.add_range(day=DAY_MAPPING[day],
                                        open_time='0:00',
                                        close_time='23:59')
            else:
                start_time = elem.xpath(
                    './/span[@class="c-hours-details-row-intervals-instance-open"]/text()').extract_first()
                end_time = elem.xpath(
                    './/span[@class="c-hours-details-row-intervals-instance-close"]/text()').extract_first()
                opening_hours.add_range(day=DAY_MAPPING[day],
                                        open_time=datetime.datetime.strptime(start_time, '%H:%M %p').strftime('%H:%M'),
                                        close_time=datetime.datetime.strptime(end_time, '%H:%M %p').strftime('%H:%M'))

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        properties = {
            'addr_full': response.xpath('//span[@itemprop="streetAddress"]/text()').extract_first(),
            'city': response.xpath('//span[@itemprop="addressLocality"]/text()').extract_first(),
            'state': response.xpath('//span[@itemprop="addressRegion"]/text()').extract_first(),
            'postcode': response.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
            'ref': response.url,
            'website': response.url,
            'lon': float(response.xpath('//span/meta[@itemprop="longitude"]/@content').extract_first()),
            'lat': float(response.xpath('//span/meta[@itemprop="latitude"]/@content').extract_first()),
        }
        phone = response.xpath('//a[@class="c-phone-number-link c-phone-main-number-link"]/text()').extract_first()
        if phone:
            properties['phone'] = phone

        hours = self.parse_hours(response.xpath('//table[@class="c-hours-details"]//tbody/tr'))

        if hours:
            properties['opening_hours'] = hours

        # hours = json.loads(response.xpath('//div[@class="c-location-hours-details-wrapper js-location-hours"]/@data-days').extract_first())
        #
        # opening_hours = self.store_hours(hours) if hours else None
        # if opening_hours:
        #     properties['opening_hours'] = opening_hours

        yield GeojsonPointItem(**properties)

    # def parse_state(self, response):
    #     urls = response.xpath('//div/ul[@class="storelist"]/li/a/@href').extract()
    #     for path in urls:
    #         yield scrapy.Request(response.urljoin(path), callback=self.parse_store)
    #
    # def parse(self, response):
    #     urls = response.xpath('//li[@class="Directory-listItem"]/a/@href').extract()
    #     for path in urls:
    #         if path.rsplit('/', 1)[-1].isnumeric():
    #             # If there's only one store, the URL will have a store number at the end
    #             yield scrapy.Request(response.urljoin(path), callback=self.parse_store)
    #         else:
    #             yield scrapy.Request(response.urljoin(path))
    #
    #     urls = response.xpath('//a[@class="c-location-grid-item-link"]/@href').extract()
    #     for path in urls:
    #         yield scrapy.Request(response.urljoin(path), callback=self.parse_store)

    def parse(self, response):
        urls = response.xpath('//li[@class="Directory-listItem"]/a/@href').extract()
        is_store_list = response.xpath('//section[contains(@class,"LocationList")]').extract()

        if not urls and is_store_list:
            urls = response.xpath('//a[contains(@class,"Teaser-titleLink")]/@href').extract()

        for url in urls:

            if re.search(r'.{2}/.+/.+',url):
                yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
            else:
                yield scrapy.Request(response.urljoin(url))
