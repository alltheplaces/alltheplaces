# -*- coding: utf-8 -*-
import scrapy
import json
from scrapy.utils.url import urljoin_rfc
from scrapy.utils.response import get_base_url

from locations.items import GeojsonPointItem

class LouisaCoffeeSpider(scrapy.Spider):
    name = "louisa_coffee"
    allowed_domains = ["www.louisacoffee.com.tw"]
    start_urls = (
        'http://www.louisacoffee.com.tw/visit_result',
    )

    def parse(self, response):
        location_hrefs = response.xpath('//a[contains(@class, "marker")]')
        for location_href in location_hrefs:
            properties = {
                'name': location_href.xpath('@rel-store-name')[0].extract(),
                'addr:full': location_href.xpath('@rel-store-address')[0].extract(),
                'ref': location_href.xpath('@rel-store-name')[0].extract(), # using the name in lieu of an ID of any kind
            }

            lon_lat = [
                float(location_href.xpath('@rel-store-lng')[0].extract()),
                float(location_href.xpath('@rel-store-lat')[0].extract()),
            ]

            yield GeojsonPointItem(
                properties=properties,
                lon_lat=lon_lat,
            )
