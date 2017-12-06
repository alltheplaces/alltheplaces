# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class BeerStoreSpider(scrapy.Spider):

    name = "beer_store"
    allowed_domains = ["www.thebeerstore.ca/"]
    start_urls = (
        'http://www.thebeerstore.ca/storelocations.json',
    )

    def parse(self, response):
        results = json.loads(response.body_as_unicode())
        features = results["features"]
        for data in features:
            description = data['properties']['description']
            end_str = "<a href"
            properties = {
                'ref': data['properties']['storeid'],
                'lon': data['geometry']['coordinates'][0],
                'lat': data['geometry']['coordinates'][1],
                'name': data['properties']['name'],
                'addr_full': description[:description.find(end_str)]
            }

            yield GeojsonPointItem(**properties)
