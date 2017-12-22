# -*- coding: utf-8 -*-
import json
import re
import scrapy

from locations.items import GeojsonPointItem

SCRIPT = 'normalize-space(//script[@type="application/ld+json"]/text())'

def replacement(match):
	return match.group().strip() + '; '

class MauriceSpider(scrapy.Spider):

    name = "maurice"
    allowed_domains = ["www.maurices.com", "locations.maurices.com"]
    download_delay = 0.2
    start_urls = (
        'https://locations.maurices.com',
    )


    def parse_store_info(self, store_info):

        s_info = json.loads(store_info.xpath(SCRIPT).extract_first())[0]
        opening_hours = s_info.get('openingHours', '')
        if opening_hours:
            hours = re.sub(r"[0-9]+ ", replacement,
                          opening_hours.strip().replace(' - ', '-'))
            hours = re.sub(r"Closed ", replacement, hours)
            opening_hours = hours.replace(": ", " ")

        props = {
            'city': s_info['address']['addressLocality'].strip(),
            'state': s_info['address']['addressRegion'].strip(),
            'ref': store_info.url,
            'website': store_info.url,
            'phone': s_info['address']['telephone'].strip(),
            'postcode': s_info['address']['postalCode'],
            'addr_full': s_info['address']['streetAddress'].strip(),
            'lat': float(s_info['geo']['latitude']),
            'lon': float(s_info['geo']['longitude']),
            'opening_hours': opening_hours,


        }
        return GeojsonPointItem(**props)

    def parse_city_stores(self, response):

        store_info_urls = response.xpath('//a[@class="store-info"]/@href').extract()
        for store in store_info_urls:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_store_info)


    def parse_state(self, response):

        city_urls = response.xpath('//div[@class="map-list-item is-single"]/a/@href').extract()
        for city in city_urls:
            yield scrapy.Request(response.urljoin(city), callback=self.parse_city_stores)

    def parse(self, response):

        state_urls = response.xpath('//div[@class="map-list-item is-single"]/a/@href').extract()
        for state in state_urls:
            yield scrapy.Request(response.urljoin(state), callback=self.parse_state)

