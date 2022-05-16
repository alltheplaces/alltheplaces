# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem


class GoodstartsSpider(scrapy.Spider):
    name = "goodstart"
    item_attributes = {
        "brand": "GoodStart Early Learning",
        "brand_wikidata": "Q24185325",
    }
    allowed_domains = ["goodstart.org.au"]
    start_urls = [
        "https://www.goodstart.org.au/extApi/CentreAPI/",
    ]

    def parse(self, response):
        data = response.json()

        for i in data["centres"]:
            properties = {
                "ref": i["NodeAliasPath"],
                "name": i["Name"],
                "addr_full": i["Address"],
                "country": "AU",
                "phone": i["Phone"],
                "lat": i["Latitude"],
                "lon": i["Longitude"],
            }

            yield GeojsonPointItem(**properties)
