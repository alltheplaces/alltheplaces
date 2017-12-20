# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class AppleSpider(scrapy.Spider):
    name = "apple"
    allowed_domains = ["apple.com"]
    start_urls = (
        'https://www.apple.com/retail/storelist/',
    )

    def store_hours(self, store_hours):
        result = ''
        for line in range(0, int(len(store_hours)/2)):
            days = re.search(r'^(\D{3})\s*((through|and|-|&|-)\s*(\D{3}))?$', store_hours[line*2])

            if (not days) or (store_hours[line*2+1] == 'Closed'):
                continue

            result += days[1][:2]
            try:
                result += "-"+days[4][:2]+" "
            except Exception as e:
                result += " "

            hours_str = store_hours[line*2+1].replace("Noon","12:00 a.m.")
            hours = re.search(r'(\d+):(\d+)\s*((a\.m\.)|(p\.m\.))\s*-\s*(\d+):?(\d+)?\s*((a\.m\.)|(p\.m\.))',hours_str)

            result += str(int(hours[1])+(12 if hours[3] in ['p.m.', 'm.p.'] else 0))+':'+hours[2]+'-'
            result += str(int(hours[6])+(12 if hours[8] in ['p.m.', 'm.p.'] else 0))+':'+hours[7]+';'
        return result.rstrip(';')

    def parse(self, response):
        shops = response.xpath('//div[@id="usstores"]//li/a/@href')
        for shop in shops:
            yield scrapy.Request(response.urljoin(shop.extract()), callback=self.parse_shops)

    def parse_shops(self, response):
            props = {
                'website': response.url,
                'ref': response.xpath('//meta[@property="og:title"]/@content').extract_first(),
                'country': 'USA',
                'opening_hours': self.store_hours(response.xpath('//div[contains(@class,"store-hours-row")]/div/text()').extract()),
            }

            phone_elem = response.xpath('//div[contains(@class,"store-details")]//span[contains(@class,"store-phone")]/text()')
            if phone_elem:
                props['phone'] = phone_elem.extract_first()

            addr_full_elem = response.xpath('//div[contains(@class,"store-details")]//span[contains(@class,"store-street")]/text()')
            if addr_full_elem:
                props['addr_full'] = addr_full_elem.extract_first()

            postcode_elem = response.xpath('//div[contains(@class,"store-details")]//span[contains(@class,"store-postal-code")]/text()')
            if postcode_elem:
                props['postcode'] = postcode_elem.extract_first()

            city_elem = response.xpath('//div[contains(@class,"store-locality")]//span[contains(@class,"store-postal-code")]/text()')
            if city_elem:
                props['city'] = city_elem.extract_first()

            state_elem = response.xpath('//div[contains(@class,"store-locality")]//span[contains(@class,"store-region")]/text()')
            if state_elem:
                props['state'] = state_elem.extract_first()

            country_elem = response.xpath('//li[@class="country-name"]/span/text()')
            if country_elem:
                props['country'] = country_elem.extract_first().strip(),

            latlon_elem = response.xpath('//div[contains(@class,"copy-software")]/a/@href')
            if latlon_elem:
                pos = re.search(r'&lat=(.+)&long=(.+)', latlon_elem.extract_first())
                props['lat'] = pos[1]
                props['lon'] = pos[2]

            yield GeojsonPointItem(**props)
