# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem

STATES = [
    'AL', 'AK', 'AS', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FM', 'FL',
    'GA', 'GU', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MH',
    'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM',
    'NY', 'NC', 'ND', 'MP', 'OH', 'OK', 'OR', 'PW', 'PA', 'PR', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VI', 'VA', 'WA', 'WV', 'WI', 'WY'
]

class JiffyLubeSpider(scrapy.Spider):
    name = "jiffylube"
    allowed_domains = ["www.jiffylube.com"]

    def start_requests(self):
        base_url = 'https://www.jiffylube.com/locations'
        for state in STATES:
            yield scrapy.Request(
                '{}/{}'.format(base_url, state)
            )
        
    def parse(self, response):
        stores = response.xpath('//div[@class="locations-by-state"]/div[@class="state-locations"]')
        for store in stores:
            ref = store.xpath('div[@class="state-location-info"]/a[@class="title"]/@href').extract_first()
            match = re.search(r'\/(\d+)', ref)
            properties = {
                "ref": match.group(1),
                "name": store.xpath('div[@class="state-location-info"]/a[@class="title"]/text()').extract_first(),
                "addr_full": store.xpath('div[@class="state-location-info"]/a[@class="address"]/div[1]/span/text()').extract_first(),
                "city": store.xpath('div[@class="state-location-info"]/a[@class="address"]/div[2]/span[@itemprop="addressLocality"]/text()').extract_first()[:2],
                "state": store.xpath('div[@class="state-location-info"]/a[@class="address"]/div[2]/span[@itemprop="addressRegion"]/text()').extract_first(),
                "postcode": store.xpath('div[@class="state-location-info"]/a[@class="address"]/div[2]/span[@itemprop="postalCode"]/text()').extract_first(),
                "phone": store.xpath('div[@class="state-location-info"]/a[@class="phone-number show"]/span[@itemprop="telephone"]/text()').extract_first(),
            }

            yield GeojsonPointItem(**properties)
