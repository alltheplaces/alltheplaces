# -*- coding: utf-8 -*-
import json
import re
import scrapy
from locations.items import GeojsonPointItem

class PizzaHutSpider(scrapy.Spider):
    name = "pizza_hut_uk"
    item_attributes = { 'brand': "Pizza Hut" }
    allowed_domains = ["pizzahut.co.uk"]
    download_delay = 0.1
    start_urls = (
        'https://www.pizzahut.co.uk/huts/',
    )

    def parse(self, response):
        urls = response.xpath('//div[@class="flex flex-wrap"]/a/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):
        ref = re.search(r'.+/(.+?)/?(?:\.html|$)', response.url).group(1)
        data = json.loads(response.xpath(
            '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()').extract_first())
        properties = {
            'ref': ref.strip('/'),
            'addr_full': data['address']['streetAddress'],
            'city': data['address']['addressLocality'],
            'state': data['address']['addressRegion'],
            'postcode': data['address']['postalCode'],
            'phone': data['telephone'],
            'name': data['name'],
            'country': 'GB',
            'lat': float(data['geo']['latitude']),
            'lon': float(data['geo']['longitude']),
            'website': data['url']
        }
        yield GeojsonPointItem(**properties)