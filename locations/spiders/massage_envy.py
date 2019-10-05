import json
import re
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

class MassageEnvySpider(scrapy.Spider):

    name = "massage_envy"
    allowed_domains = ["locations.massageenvy.com"]
    start_urls = (
        'https://locations.massageenvy.com/index.html',
    )

    def normalize_hours(self, hours):
        o = OpeningHours()

        for hour in hours:
            if hour.get('holidayHoursIsRegular') == False:
                continue

            short_day = hour['day'].title()[:2]

            for r in hour['intervals']:
                open_time = '%04d' % r['start']
                close_time = '%04d' % r['end']

                o.add_range(short_day, open_time, close_time, '%H%M')

        return o.as_opening_hours()

    def parse_location(self, response):
        opening_hours = response.css('.js-location-hours').xpath('@data-days').extract_first()
        if opening_hours:
            opening_hours = json.loads(opening_hours)
            opening_hours = self.normalize_hours(opening_hours)

        props = {
            'addr_full': ' '.join(i.strip() for i in response.xpath('//div[@class="info-right hidden-xs"]/div/address[@itemprop="address"]/span[@itemprop="streetAddress"]/span/text()').extract()),
            'lat': float(response.xpath('//meta[@itemprop="latitude"]/@content').extract_first().strip()),
            'lon': float(response.xpath('//meta[@itemprop="longitude"]/@content').extract_first().strip()),
            'city': response.xpath('//div[@class="info-right hidden-xs"]/div/address[@itemprop="address"]/span/span[@itemprop="addressLocality"]/text()').extract_first().strip(),
            'postcode': response.xpath('//div[@class="info-right hidden-xs"]/div/address[@itemprop="address"]/span[@itemprop="postalCode"]/text()').extract_first().strip(),
            'state': response.xpath('//div[@class="info-right hidden-xs"]/div/address[@itemprop="address"]/abbr[@itemprop="addressRegion"]/text()').extract_first().strip(),
            'phone': response.xpath('//span[@itemprop="telephone"]/text()').extract_first().strip(),
            'ref': response.url,
            'website': response.url,
            'opening_hours': opening_hours
        }
        return GeojsonPointItem(**props)

    def parse(self, response):
        for state in response.xpath('//a[@class="c-directory-list-content-item-link"]/@href').extract():
            yield scrapy.Request(
                url=response.urljoin(state),
            )

        if response.xpath('//span[@itemprop="telephone"]'):
            yield self.parse_location(response)
