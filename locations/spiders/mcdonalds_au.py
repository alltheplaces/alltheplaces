# -*- coding: utf-8 -*-

import scrapy

from locations.items import GeojsonPointItem


class McDonaldsAUSpider(scrapy.Spider):
    name = "mcdonalds_au"
    item_attributes = {"brand": "McDonald's", "brand_wikidata": "Q38076"}
    allowed_domains = ["mcdonalds.com.au"]
    start_urls = [
        "https://mcdonalds.com.au/data/store",
    ]

    def parse(self, response):
        data = response.json()

        for store in data:
            try:
                properties = {
                    "name": store["title"],
                    "ref": store["store_code"],
                    "addr_full": store["store_address"],
                    "city": store["store_suburb"],
                    "state": store["store_state"],
                    "postcode": store["store_postcode"],
                    "country": "AU",
                    "phone": store["store_phone"],
                    "website": response.url,
                    "lat": float(store["lat_long"]["lat"]),
                    "lon": float(store["lat_long"]["lon"]),
                }
                yield GeojsonPointItem(**properties)
            except:
                pass
