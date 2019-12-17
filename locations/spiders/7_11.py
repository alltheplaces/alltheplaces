# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class SevenElevenSpider(scrapy.Spider):
    name = "seven_eleven"
    brand = '7-Eleven'
    allowed_domains = [
                        "www.7-eleven.com",
                        "api.7-eleven.com"
                        ]
    start_urls = (
        'https://www.7-eleven.com/locations',
    )

    def parse_hours(self, hours):
        if hours.xpath('./div/text()').extract_first() == "Open 24/7":
            return '24/7'
        else:
            opening_hours = OpeningHours()
            hours = hours.xpath('./meta[@itemprop="openingHours"]/@content').extract()
            for hour in hours:
                try:
                    day, open_time, close_time = re.search(r'([A-Za-z]{2})\s([\d:]+)\s-\s([\d:]+)', hour).groups()
                except:
                    continue
                opening_hours.add_range(day=day, open_time=open_time, close_time=close_time, time_format='%H:%M')

            return opening_hours.as_opening_hours()

    def parse_store(self, response):
        properties = {
            'ref': "_".join(re.search(r".+/(.+?)/(.+?)/(.+?)/?(?:\.html|$)", response.url).groups()),
            'addr_full': response.xpath('normalize-space(//span[@itemprop="streetAddress"]//text())').extract_first().upper(),
            'city': response.xpath('normalize-space(//span[@itemprop="addressLocality"]//text())').extract_first(),
            'state': response.xpath('normalize-space(//abbr[@itemprop="addressRegion"]//text())').extract_first(),
            'postcode': response.xpath('normalize-space(//span[@itemprop="postalCode"]//text())').extract_first(),
            'country': response.xpath('normalize-space(//meta[@itemprop="addressCountry"]/@content)').extract_first(),
            'phone': response.xpath('normalize-space(//*[@itemprop="telephone"]//text())').extract_first(),
            'website': response.url,
            'lat': response.xpath('normalize-space(//meta[@itemprop="latitude"]/@content)').extract_first(),
            'lon': response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').extract_first(),
        }
        
        properties['opening_hours'] = self.parse_hours(response.xpath('//div[@id="se-local-store-hours"]'))
        
        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath('//div[contains(@class, "locations-specifics")]//li/a/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url))

        if not urls:
            stores = response.xpath('//div[@class="location"]')
            for store in stores:
                url = store.xpath('.//a[contains(@class, "se-local-store")]/@href').extract_first()
                yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
