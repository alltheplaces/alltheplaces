# -*- coding: utf-8 -*-

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


class SpecsaversSpider(scrapy.Spider):
    download_delay = 5
    name = "specsavers"
    allowed_domains = ['specsavers.co.uk']
    start_urls = [
        'https://www.specsavers.co.uk/stores/full-store-list',
    ]

    def parse_hours(self, elements):
        opening_hours = OpeningHours()

        for elem in elements:
            day = elem.split(" ")[0]
            hours = elem.split(" ")[1:]

            if hours[0] == "Closed":
                continue
            elif hours[0] == "Open 24 hours":
                opening_hours.add_range(day=DAY_MAPPING[day],
                                        open_time='0:00',
                                        close_time='23:59')
            else:
                start_time = hours[0]
                end_time = hours[2]
                opening_hours.add_range(day=DAY_MAPPING[day],
                                        open_time=start_time,
                                        close_time=end_time)

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        lat, lon = '', ''

        try:
            lat = float(
                response.xpath('//div[contains(@class,"aui-store-page")]/@data-store-geo-loc-lat').extract_first())
            lon = float(
                response.xpath('//div[contains(@class,"aui-store-page")]/@data-store-geo-loc-lng').extract_first())
        except:
            pass

        properties = {
            'addr_full': response.xpath('//span[@itemprop="streetAddress"]/text()').extract_first(),
            'phone': response.xpath('//span[@class="contact--store-telephone--text"]/text()').extract_first(),
            'city': response.xpath('//span[@itemprop="addressLocality"]/text()').extract_first(),
            'state': response.xpath('//span[@itemprop="addressRegion"]/text()').extract_first(),
            'postcode': response.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
            'country': "GB",
            'ref': response.url,
            'website': response.url,
            'lat': lat,
            'lon': lon,
            'name': response.xpath('//h1[@class="store-header--title"]/text()').extract_first()
        }

        hours = self.parse_hours(response.xpath('//tr[@itemprop="openingHours"]/@content').extract())

        if hours:
            properties['opening_hours'] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath('//div[contains(@class,"view-full-store-list")]/div/div/div/div/ul/li/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
