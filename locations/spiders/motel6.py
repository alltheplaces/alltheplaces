# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem

brand_lookup = {"MS": "Motel 6", "SS": "Studio 6", "HS": "Hotel 6"}


class Motel6Spider(scrapy.Spider):
    name = "motel6"
    allowed_domains = ["motel6.com"]
    start_urls = ("https://www.motel6.com/content/g6-cache/property-summary.1.json",)

    def parse(self, response):
        idata = response.json()
        url = "https://www.motel6.com/bin/g6/propertydata.{}.json"

        for storeid in idata.keys():
            try:
                int(storeid)
            except ValueError:
                continue

            try:
                yield scrapy.Request(url.format(storeid), callback=self.parse_hotel)
            except ValueError:
                continue

    def parse_hotel(self, response):
        mdata = response.json()

        properties = {
            "ref": mdata["property_id"],
            "name": mdata["name"],
            "addr_full": mdata["address"],
            "city": mdata["city"],
            "postcode": mdata["zip"],
            "lat": mdata["latitude"],
            "lon": mdata["longitude"],
            "phone": mdata["phone"],
            "state": mdata["state"],
            "website": mdata["microsite_url"],
            "brand": brand_lookup[mdata["brand_id"]],
        }

        yield GeojsonPointItem(**properties)
