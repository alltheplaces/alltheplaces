# -*- coding: utf-8 -*-
import re

import scrapy
import json

from locations.items import GeojsonPointItem


class RedRoosterSpider(scrapy.Spider):
    # download_delay = 0.2
    name = "redrooster_au"
    item_attributes = {"brand": "Red Rooster", "brand_wikidata": "Q376466"}
    allowed_domains = ["redrooster.com.au"]
    start_urls = ("https://www.redrooster.com.au/api/stores/4/",)

    def parse(self, response):
        data = response.json()

        for i in data:
            properties = {
                "ref": i["storeNumber"],
                "name": i["title"],
                "street_address": i["address"],
                "city": i["suburb"],
                "state": i.get("state"),
                "postcode": i["postcode"],
                "country": "AU",
                "phone": i["phone"],
                "lat": i["latitude"],
                "lon": i["longitude"],
            }

            yield GeojsonPointItem(**properties)
