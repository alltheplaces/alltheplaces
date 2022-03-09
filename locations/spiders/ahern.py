# -*- coding: utf-8 -*-
import re

import scrapy
import json

from locations.items import GeojsonPointItem


class SCSpider(scrapy.Spider):
    # download_delay = 0.2
    name = "ahern"
    item_attributes = {"brand": "Ahern Rentals"}
    allowed_domains = ["ahern.com"]
    start_urls = ("https://www.ahern.com/assets/js/storeLocator/data/locations.json",)

    def parse(self, response):
        data = json.loads(json.dumps(response.json()))

        for i in data:

            properties = {
                "ref": i["id"],
                "name": i["name"],
                "addr_full": i["address"] + i["address2"],
                "city": i["city"],
                "state": i["state"],
                "postcode": i["postal"],
                "country": "US",
                "phone": i["phone"],
                "lat": float(i["lat"]),
                "lon": float(i["lng"]),
            }

            yield GeojsonPointItem(**properties)
