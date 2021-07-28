# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
DAY_MAPPING = {
    'Monday': 'Mo',
    'Tuesday': 'Tu',
    'Wednesday': 'We',
    'Thursday': 'Th',
    'Friday': 'Fr',
    'Saturday': 'Sa',
    'Sunday': 'Su'
}


class IkeaUKSpider(scrapy.Spider):
    name = "ikea_uk"
    item_attributes = {'brand': "Ikea"}
    allowed_domains = ["ikea.com"]
    start_urls = (
        'http://www.ikea.com/gb/en/store/',
    )

    def store_hours(self, store_hours):
        opening_hours = OpeningHours()
        store_hours = store_hours.xpath('.//h3[contains(strong, "Store")]/following-sibling::p[1]')
        weekdays = store_hours.xpath('.//strong/text()').extract()
        weekday_hours = store_hours.xpath('.//strong/following-sibling::text()').extract()
        if '\u200b' in weekdays:
            weekdays.remove('\u200b')
        weekday_data = list(zip(weekdays, weekday_hours))
        for weekday in weekday_data:
            day_range, day_hours = weekday
            day_hours = day_hours.replace('–', '-')
            day_range = day_range.replace('–', '-')
            day_range = day_range.strip().strip('\u200b').strip(':').strip(' -').split(' - ')
            open_time, close_time = day_hours.split(' - ')
            open_time = open_time.strip().strip('\u200b')
            close_time = close_time.strip().strip('\u200b')

            if len(day_range) > 1:
                start = DAYS.index(day_range[0])
                end = DAYS.index(day_range[1])
                for day in DAYS[start:end]:
                    opening_hours.add_range(day=DAY_MAPPING[day], open_time=open_time,
                                            close_time=close_time,
                                            time_format='%H:%M')
            else:
                opening_hours.add_range(day=DAY_MAPPING[day_range[0]], open_time=open_time,
                                        close_time=close_time,
                                        time_format='%H:%M')

        return opening_hours.as_opening_hours()

    def parse(self, response): 
        shops_urls = response.xpath('//article//a[contains(@href, "stores")]/@href').extract()
        for shop_url in shops_urls:
            yield scrapy.Request(url=shop_url, callback=self.parse_shops)

    def parse_shops(self, response):
        ref = re.search(r'.+/(.+?)/?(?:\.html|$)', response.url).group(1)
        address_full = response.xpath('//h3[contains(strong, "Address")]/following-sibling::p/text()').extract_first()
        name = response.xpath('//h1[@class="c1m1sl8e pub__h1 s1gshh7t"]/text()').extract_first()

        properties = {
            'ref': ref,
            'name': name,
            'addr_full': address_full,
            'country': 'GB',
            'website': response.url
        }
        hours = response.xpath('.//h2[contains(strong, "Opening hours")]/following::div[1]')

        if hours:
            properties['opening_hours'] = self.store_hours(hours)

        yield GeojsonPointItem(**properties)
