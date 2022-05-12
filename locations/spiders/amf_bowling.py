# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class AMFBowlingSpider(scrapy.Spider):
    name = "amf_bowling"
    item_attributes = {"brand": "AMF Bowling Center", "brand_wikidata": "Q4652616"}
    start_urls = ("https://www.amf.com/bowlero-location/finder?_format=json",)

    def parse(self, response):
        for location in json.loads(response.body):
            yield GeojsonPointItem(
                name=location["name"],
                ref=location["id"],
                addr_full=location["address1"],
                lat=location["lat"],
                lon=location["lng"],
                city=location["city"],
                state=location["state"],
                postcode=location["zip"],
                country="USA",
                phone=location["phone"],
                website=location["url"],
            )
