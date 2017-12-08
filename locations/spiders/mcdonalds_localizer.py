# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem


class McLocalizer(scrapy.Spider):

    name = "mclocalizer"
    allowed_domains = ["www.mcdonalds.com", "www.mcdonalds.com.pr", "www.mcdonalds.co.cr"]
    start_urls = (
        'http://www.mcdonalds.com.pr/api/restaurantsByCountry?country=PR',
        'http://www.mcdonalds.co.cr/api/restaurantsByCountry?country=CR',
    )

    def parse(self, response):
        data = response.body_as_unicode()
        data.replace('" ', '"')
        data.replace(' "', '"')
        results = json.loads(data)
        results = results["content"]["restaurants"]
        for data in results:
            properties = {
                'ref': data['id'],
                'lon': data['longitude'],
                'lat': data['latitude'],
                'name': data['name'][:data['name'].find("<br")]
            }

            yield GeojsonPointItem(**properties)