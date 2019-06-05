# -*- coding: utf-8 -*-
import scrapy
import re
import json
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


day_mapping = {'Monday': 'Mo', 'Tuesday': 'Tu', 'Wednesday': 'We', 'Thursday': 'Th', 'Friday': 'Fr', 'Saturday': 'Sa',
               'Sunday': 'Su'}


class LowesSpider(scrapy.Spider):
    """"This spider scrapes Lowes retail store locations"""
    name = "lowes"
    allowed_domains = ["lowes.com"]
    start_urls = ('http://www.lowes.com/Lowes-Stores',)
    download_delay = 0.5

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36',
    }

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()

        for weekday in store_hours:
            day = weekday.get('day').get('day')
            open_time = weekday.get('day').get('open')
            hour, minute, sec = open_time.split('.')
            open_time_formatted = hour + ':' + minute

            close = weekday.get('day').get('close')
            hour, minute, sec = close.split('.')
            close_time_formatted = hour + ':' + minute

            if close_time_formatted in {'00:00', '24:00'}:
                close_time_formatted = "23:59"

            opening_hours.add_range(day=day_mapping[day],
                                    open_time=open_time_formatted,
                                    close_time=close_time_formatted)

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        ref = re.search(r'.+/(.+)', response.url).group(1)

        script_content = response.xpath('//*[@id="wrapper"]/script[1]').extract_first()
        script_data = re.search(r'currentStore: (.*)userLocation:', script_content,
                                flags=re.IGNORECASE | re.DOTALL).group(1).strip()
        script_data = script_data.strip(",")
        script_data = script_data.replace("\'", "")

        json_data = json.loads(script_data)
        store_hours = json_data.get('storeHours')

        properties = {
            'lat': float(json_data.get('lat')),
            'lon': float(json_data.get('long')),
            'ref': ref,
            'addr_full': response.xpath('normalize-space(//span[@itemprop="streetAddress"]/text())').extract_first(),
            'city': response.xpath('normalize-space(//span[@itemprop="addressLocality"]/text())').extract_first(),
            'state': response.xpath('normalize-space(//span[@itemprop="addressRegion"]/text())').extract_first(),
            'postcode': response.xpath('normalize-space(//span[@itemprop="postalCode"]/text())').extract_first(),
            'phone': response.xpath('normalize-space(//span[@itemprop="telephone"]/text())').extract_first(),
            'website': response.request.url,
            'opening_hours': self.parse_hours(store_hours),
        }

        yield GeojsonPointItem(**properties)

    def parse_state(self, response):
        city_urls = response.xpath('//div[@class="v-spacing-small"]/a/@href').extract()
        for path in city_urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_store)

    def parse(self, response):
        urls = response.xpath('//li[@role="listitem"]/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
