# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class New_york_friesSpider(scrapy.Spider):
    name = "new_york_fries"
    item_attributes = {"brand": "New York Fries"}
    allowed_domains = ["newyorkfries.com"]
    start_urls = [
        "https://www.newyorkfries.com/locations/all",
    ]

    def parse(self, response):
        data = response.xpath(
            '//script[contains(.,"canadaEntries")]/text()'
        ).extract_first()

        places_ca = re.search(r"canadaEntries\s=\s(.*)", data).groups()[0]

        places_ca = json.loads(places_ca)

        for place in places_ca:
            properties = {
                "ref": place["id"],
                "name": place["title"],
                "addr_full": place["address"],
                "city": place["city"],
                "state": place["province"],
                "country": place["country"],
                "lat": place["latitude"],
                "lon": place["longitude"],
                "website": place["url"],
            }

            yield GeojsonPointItem(**properties)

        places_intl = re.search(r"intlEntries\s=\s(.*)", data).groups()[0]

        places_intl = json.loads(places_intl)

        for place in places_intl:
            properties = {
                "ref": place["id"],
                "name": place["title"],
                "addr_full": place["address"],
                "city": place["city"],
                "state": place["province"],
                "country": place["country"],
                "lat": place["latitude"],
                "lon": place["longitude"],
                "website": place["url"],
            }

            yield GeojsonPointItem(**properties)
