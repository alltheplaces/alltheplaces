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
        for region_name in results["cafes"]:
            for store_data in results["cafes"][region_name]:

                address_string = store_data['address'].replace('\n', ' ').replace('\r', '').replace('<br>', ', ')
                address_data = address_string.split(", ")

                properties = {
                    'name': store_data['name'],
                    'addr:full': address_string,
                    'addr:city': address_string.split(", ")[1].replace(" ", ""),
                    'region': store_data['region'].title(),
                    'website': store_data['url'],
                    'ref': store_data['id'],
                }
                lon_lat = [
                    store_data['longitude'],
                    store_data['latitude'],
                ]

                yield GeojsonPointItem(
                    properties=properties,
                    lon_lat=lon_lat,
                )