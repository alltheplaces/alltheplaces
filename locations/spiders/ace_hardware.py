import scrapy
import re
import json
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']


class AceHardwareSpider(scrapy.Spider):
    name = "ace_hardware"
    brand = "Ace Hardware"
    allowed_domains = ["www.acehardware.com"]
    download_delay = 0.1
    start_urls = (
        'https://www.acehardware.com/store-directory',
    )

    def parse_hours(self, lis):
        o = OpeningHours()

        for day in DAY_MAPPING:
            d = day.title()[:2]

            label = lis[day]['label']
            if label == '0000 - 0000':
                continue

            start, end = label.split(' - ')
            start = '%s:%s' % (start[:2], start[2:])
            end = '%s:%s' % (end[:2], end[2:])

            o.add_range(d, start, end)
        return o.as_opening_hours()

    def parse_store(self, response):
        store_data = response.xpath('//script[@id="data-mz-preload-store"]/text()').extract_first()

        if not store_data:
            return

        store_data = json.loads(store_data)

        properties = {
            'name': store_data['StoreName'],
            'phone': store_data['Phone'],
            'addr_full': store_data['StoreAddressLn1'],
            'city': store_data['StoreCityNm'],
            'state': store_data['StoreStateCd'],
            'postcode': store_data['StoreZipCd'],
            'ref': store_data['StoreNumber'],
            'website': response.url,
            'lat': float(store_data['Latitude']),
            'lon': float(store_data['Longitude']),
        }

        hours = self.parse_hours(store_data['RegularHours'])
        if hours:
            properties['opening_hours'] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        for store_url in response.css('div.store-directory-list-item').xpath('div/a/@href').extract():
            yield scrapy.Request(
                response.urljoin(store_url),
                callback=self.parse_store,
            )
