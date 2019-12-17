# -*- coding: utf-8 -*-
import datetime
import re

import scrapy
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


class TGIFridaySpider(scrapy.Spider):
    download_delay = 0.2
    name = "tgifridays"
    chain_name = "TGI Friday's"
    allowed_domains = ["tgifridays.com"]
    start_urls = (
        'https://locations.tgifridays.com/index.html',
    )

    def parse_hours(self, elements):
        opening_hours = OpeningHours()

        for elem in elements:
            day = elem.xpath('.//td[@class="c-location-hours-details-row-day"]/text()').extract_first()
            intervals = elem.xpath('.//td[@class="c-location-hours-details-row-intervals"]')

            if intervals.xpath('./text()').extract_first() == "Closed":
                continue
            if intervals.xpath('./span/text()').extract_first() == "Open 24 hours":
                opening_hours.add_range(day=DAY_MAPPING[day],
                                        open_time='0:00',
                                        close_time='23:59')
            else:
                start_time = elem.xpath(
                    './/span[@class="c-location-hours-details-row-intervals-instance-open"]/text()').extract_first()
                end_time = elem.xpath(
                    './/span[@class="c-location-hours-details-row-intervals-instance-close"]/text()').extract_first()
                opening_hours.add_range(day=DAY_MAPPING[day],
                                        open_time=datetime.datetime.strptime(start_time, '%H:%M %p').strftime('%H:%M'),
                                        close_time=datetime.datetime.strptime(end_time, '%H:%M %p').strftime('%H:%M'))
        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        ref = re.search(r'.+/(.+).html', response.url).group(1)

        properties = {
            'addr_full': response.xpath('//span[@class="c-address-street-1"]/text()').extract_first().strip(),
            'phone': response.xpath('//span[@class="Phone"]//span[@class="Phone-link"]/text()').extract_first(),
            'city': response.xpath('//span[@itemprop="addressLocality"]/text()').extract_first(),
            'state': response.xpath('//abbr[@itemprop="addressRegion"]/text()').extract_first(),
            'postcode': response.xpath('//span[@itemprop="postalCode"]/text()').extract_first().strip(),
            'country': response.xpath('//abbr[@itemprop="addressCountry"]/text()').extract_first(),
            'ref': ref,
            'website': response.url,
            'lat': float(response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()),
            'lon': float(response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()),
            'name': response.xpath('//span[@id="location-name"]/span[@class="LocationName-geo"]/text()').extract_first()
        }
        hours = self.parse_hours(response.xpath('//table[@class="c-location-hours-details"]//tbody/tr'))

        if hours:
            properties['opening_hours'] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath('//a[@class="c-directory-list-content-item-link"]/@href').extract()
        is_store_list = response.xpath('//div[@class="LocationList"]').extract()

        if not urls and is_store_list:
            urls = response.xpath('//div[@class="LocationList"]//a[@class="Teaser-titleName"]/@href').extract()
        for url in urls:
            if url.count('/') >= 2:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
            else:
                yield scrapy.Request(response.urljoin(url))
