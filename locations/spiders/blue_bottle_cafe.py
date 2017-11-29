# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem

class BlueBottleCafeSpider(scrapy.Spider):
    name = "bluebottlecafe"
    allowed_domains = ["www.bluebottlecoffee.com"]
    start_urls = (
        'https://bluebottlecoffee.com/api/cafe_search/fetch.json?coordinates=false&query=true&search_value=all',
    )
    def parse(self, response):
        results = json.loads(response.body_as_unicode())
        for e in results["cafes"]:
            for store_data in results["cafes"][e]:

                add = store_data['address'].replace('\n', ' ').replace('\r', '').replace('<br>', ',')
                properties = {
                    'name': store_data['name'],
                    'addr:full': add,
                    'addr:city': store_data['region'],
                    'website': store_data['url'],
                    'ref': store_data['id'],
                }
                lon_lat = [
                    float(store_data['longitude']),
                    float(store_data['latitude']),
                ]

                yield GeojsonPointItem(
                    properties=properties,
                    lon_lat=lon_lat,
                )