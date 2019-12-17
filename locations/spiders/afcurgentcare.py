import json
import re
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

class AfcUrgentCareSpider(scrapy.Spider):
    name = "afcurgentcare"
    item_attributes = { 'brand': "AFC Urgent Care" }
    allowed_domains = ["afcurgentcare.com"]
    download_delay = 0.2
    start_urls = (
        'https://www.afcurgentcare.com/locations/',
    )

    def parse(self, response):
        for url in response.xpath('//li[@class="location"]/@data-href').extract():
            yield scrapy.Request(
                response.urljoin(url),
                callback=self.parse_store,
            )

    def parse_store(self, response):
        properties = {
            'ref': response.url,
            'lat': response.xpath('//div[@class="map-container"]/div/@data-latitude').extract_first(),
            'lon': response.xpath('//div[@class="map-container"]/div/@data-longitude').extract_first(),
            'phone': response.xpath('//a[@class="phone-link"]/span/text()').extract_first(),
            'addr_full': response.xpath('//span[@itemprop="streetAddress"]/text()').extract_first().strip(),
            'name': response.xpath('//meta[@itemprop="name legalName"]/@content').extract_first(),
            'city': response.xpath('//span[@itemprop="addressLocality"]/text()').extract_first()[:-1],
            'state': response.xpath('//span[@itemprop="addressRegion"]/text()').extract_first().strip(),
            'postcode': response.xpath('//span[@itemprop="postalCode"]/text()').extract_first().strip(),
        }

        o = OpeningHours()
        for h in response.css('#LocalMapAreaOpenHourBanner li.h-day'):
            day = h.xpath('em/span/text()').extract_first().strip()[:2]
            day_range = h.xpath('em/text()').extract_first().strip(':').strip()
            open_time, close_time = day_range.split(' - ')

            o.add_range(day, open_time, close_time, '%I:%M %p')
        properties['opening_hours'] = o.as_opening_hours()

        yield GeojsonPointItem(**properties)
