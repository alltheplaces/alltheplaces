# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class PriceRiteSpider(scrapy.Spider):
    name = "pricerite"
    allowed_domains = ["priceritesupermarkets.com"]

    start_urls = (
        "https://www.priceritesupermarkets.com/locations/",
    )

    def parse(self, response):
        script = response.xpath('//script[contains(text(), "var stores")]').extract_first()
        stores = json.loads(re.search(r'var stores = (.*?);', script).groups()[0])

        for store in stores:
            properties = {
                "ref": store["storeNumber"],
                "name": store["name"],
                "lat": store["latitude"],
                "lon": store["longitude"],
                "addr_full": store["address1"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zipCode"],
            }

            yield GeojsonPointItem(**properties)

