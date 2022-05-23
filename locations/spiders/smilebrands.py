# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class SmilebrandsSpider(scrapy.Spider):
    name = "smilebrands"
    item_attributes = {"brand": "Smile Brands Inc.", "brand_wikidata": "Q108286823"}
    allowed_domains = ["smilebrands.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = [
        "https://smilebrands.com/wp-admin/admin-ajax.php?action=store_search&lat=39.11553&lng=-94.62679&max_results=100000&search_radius=100&autoload=1",
    ]

    def parse(self, response):
        for place in response.json():
            properties = {
                "name": place["store"],
                "ref": place["address"],
                "addr_full": place["address"],
                "city": place["city"],
                "state": place["state"],
                "postcode": place["zip"],
                "country": "US",
                "lat": place["lat"],
                "lon": place["lng"],
                "website": place["url"],
            }

            yield GeojsonPointItem(**properties)
