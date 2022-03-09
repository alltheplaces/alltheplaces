# -*- coding: utf-8 -*-
import re
import json
import scrapy
from locations.items import GeojsonPointItem


class BunningsSpider(scrapy.Spider):
    name = "bunnings"
    allowed_domains = ["bunnings.com.au"]
    start_urls = ("https://www.bunnings.com.au/stores/",)

    def parse(self, response):
        raw_data = re.search(
            "com_bunnings_locations_mapLocations = (.+);",
            response.text,
        ).group(1)
        stores = json.loads(raw_data)

        for idx, store in enumerate(stores):
            store = store["Store"]
            properties = {
                "lat": store["Location"]["Latitude"],
                "lon": store["Location"]["Longitude"],
                "name": store["StoreName"],
                "addr_full": f'{store["Address"]["Address"]} {store["Address"]["AddressLineTwo"]}'.strip(),
                "city": store["Address"]["Suburb"],
                "state": store["Address"]["State"],
                "postcode": store["Address"]["Postcode"],
                "country": "AU",
                "phone": store["Phone"],
                "website": response.urljoin(store["StoreUrl"]),
                "ref": idx,
            }
            yield GeojsonPointItem(**properties)
