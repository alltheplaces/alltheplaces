# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class Forever21Spider(scrapy.Spider):
    name = "forever21"
    item_attributes = {
        "brand": "Forever 21",
        "brand_wikidata": "Q1060537",
    }
    allowed_domains = ["forever21.com"]
    start_urls = [
        "https://www.forever21.com/on/demandware.store/Sites-forever21-Site/en_US/Stores-FindStores?showMap=false&radius=10000&lat=45&long=-104",
    ]

    def parse(self, response):
        for row in response.json()["stores"]:
            properties = {
                "ref": row["ID"],
                "lat": row["latitude"],
                "lon": row["longitude"],
                "name": row["name"],
                "street_address": row["address1"],
                "city": row["city"],
                "state": row["stateCode"],
                "country": row["countryCode"],
            }
            yield GeojsonPointItem(**properties)
