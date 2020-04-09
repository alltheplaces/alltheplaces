# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class CircleKSpider(scrapy.Spider):

    name = "circle_k"
    item_attributes = { 'brand': "Circle K", 'brand_wikidata': "Q3268010" }
    allowed_domains = ["www.circlek.com"]

    start_urls = (
        'https://www.circlek.com/stores_new.php?lat=30.352998399999997&lng=-97.79609599999999&distance=80000&services=&region=global',
    )

    def parse(self, response):
        results = json.loads(response.body_as_unicode())

        for storeid, store in results['stores'].items():
            yield scrapy.Request(url=response.urljoin(store['url']), callback=self.parse_state,
                                 meta={'ref': store['cost_center'], 'addr_full': store['address'],
                                       'city': store['city'], 'country': store['country'], 'lat': store['latitude'],
                                       'lon': store['longitude']})

    def parse_state(self, response):
        ## Not all countries/store pages follow the same format
        if response.meta['country'] == 'US':
            state = response.xpath('//*[@class="heading-small"]/span[2]/text()').extract_first()
            postal = response.xpath('//*[@class="heading-small"]/span[3]/text()').extract_first()
        elif response.meta['country'] in ['CA', 'Canada']:
            if len(response.xpath('//*[@class="heading-small"]/span[2]/text()').extract_first()) < 4:
                state = response.xpath('//*[@class="heading-small"]/span[2]/text()').extract_first()
                postal = response.xpath('//*[@class="heading-small"]/span[3]/text()').extract_first()
            else:
                state = ""
                postal = response.xpath('//*[@class="heading-small"]/span[2]/text()').extract_first()
        else:
            state = ""
            postal = response.xpath('//*[@class="heading-small"]/span[2]/text()').extract_first()

        properties = {
            'ref': response.meta['ref'],
            'name': 'Circle K',
            'addr_full': response.meta['addr_full'],
            'city': response.meta['city'],
            'state': state,
            'postcode': postal,
            'country': response.meta['country'],
            'lat': response.meta['lat'],
            'lon': response.meta['lon'],
            'website': response.url
        }

        yield GeojsonPointItem(**properties)
