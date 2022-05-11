# -*- coding: utf-8 -*-
import scrapy
import json
from locations.brands import Brand
from locations.seo import extract_details, join_address_fields


class GreggsSpider(scrapy.Spider):

    name = "greggs"
    brand = Brand.from_wikidata('Greggs', 'Q3403981')
    start_urls = ['https://production-digital.greggs.co.uk/api/v1.0/shops?latitude=53&longitude=-2&distanceInMeters=600000']

    def parse(self, response):
        for store in json.loads(response.body):
            item = self.brand.item()
            extract_details(item, store['address'])
            item['name'] = store['shopName']
            item['ref'] = store['shopCode']
            item['street_address'] = join_address_fields(store['address'], 'houseNumberOrName', 'streetName')
            yield item
