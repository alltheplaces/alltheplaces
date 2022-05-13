# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class Clinical_pathology_laboratoriesSpider(scrapy.Spider):
    name = "clinical_pathology_laboratories"
    item_attributes = {
        "brand": "Clinical Pathology Laboratories",
        "brand_wikidata": "Q91911320",
    }
    allowed_domains = ["cpllabs.com"]
    start_urls = [
        "https://www.zeemaps.com/emarkers?g=3025292&k=REGULAR&e=true&_dc=0.9710587730049409",
    ]

    def parse(self, response):
        data = response.json()
        for i, item in enumerate(data):
            properties = {
                "name": item["nm"],
                "addr_full": item["s"],
                "city": item["city"],
                "state": item["state"],
                "postcode": item["zip"],
                "country": "US",
                "ref": item["id"],
                "website": "na",
                "lat": item["lat"],
                "lon": item["lng"],
            }
            yield GeojsonPointItem(**properties)
