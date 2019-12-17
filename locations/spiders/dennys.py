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
    chain_name = "Denny's"
    allowed_domains = ["locations.dennys.com"]
    start_urls = (
        'https://locations.dennys.com/',
    )


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
            'addr_full': response.xpath('//meta[@itemprop="streetAddress"]/@content').extract_first(),
            'city': response.xpath('//meta[@itemprop="addressLocality"]/@content').extract_first(),
            'state': response.xpath('//abbr[@itemprop="addressRegion"]/text()').extract_first(),
            'postcode': response.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
            'ref': response.url,
            'website': response.url,
            'lon': float(response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()),
            'lat': float(response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()),
        }
        phone = response.xpath('//div[@itemprop="telephone"]/text()').extract_first()
        if phone:
            properties['phone'] = phone

        hours = self.parse_hours(response.xpath('//table[@class="c-hours-details"]//tbody/tr'))

        if hours:
            properties['opening_hours'] = hours

        yield GeojsonPointItem(**properties)


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
