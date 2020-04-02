# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class Royal_farmsSpider(scrapy.Spider):
    name = "royal_farms"
    item_attributes = {'brand': 'Royal Farms'}
    allowed_domains = ['royalfarms.com']
    start_urls = [
        'https://www.royalfarms.com/location_results.asp',
    ]

    def parse(self, response):
        states = response.xpath('//select[@id="state"]/option/@value').extract()

        url = 'https://www.royalfarms.com/location_results.asp'

        for state in states:
            if state:
                form_data = {'submitStore': 'yes', 'state': state}

                yield scrapy.http.FormRequest(
                    url=url,
                    method='POST',
                    formdata=form_data,
                    callback=self.parse_stores
                )

    def parse_stores(self, response):
        stores = response.xpath('//tr[@class="listdata"]/td[@class="listdata"][1]')

        for store in stores:
            store_number = store.xpath('./strong/text()').re_first(r'STORE #(\d+)')
            addr_parts = store.xpath('./text()').extract()
            addr_parts = list(filter(None, [x.replace('\xa0', ' ').strip() for x in addr_parts]))
            phone = addr_parts.pop(-1)
            last_line = addr_parts.pop(-1)
            city, state, postal = re.search(r'(.+?), ([A-Z]{2}) (\d{5})', last_line).groups()
            address = " ".join(addr_parts)

            properties = {
                'ref': store_number,
                'addr_full': address,
                'city': city,
                'state': state,
                'postcode': postal,
                'country': 'US',
                'phone': phone
            }

            yield GeojsonPointItem(**properties)
