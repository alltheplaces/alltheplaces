# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem


class McDonaldsPR(scrapy.Spider):

    name = "mcdonalds_pr"
    allowed_domains = ["www.mcdonalds.com.pr", "www.mcdonalds.com"]
    start_urls = (
        'http://www.mcdonalds.com.pr/api/restaurantsByCountry?country=PR',
    )

    def parse(self, response):
        results = json.loads(response.body_as_unicode())
        results = results["content"]["restaurants"]
        for data in results:
            properties = {
                'ref': data['id'],
                'lon': data['longitude'],
                'lat': data['latitude'],
                'name': data['name'][:data['name'].find("<br")]
            }

            yield GeojsonPointItem(**properties)
