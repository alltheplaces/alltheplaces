# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem

brand_lookup = {
    "MS": "Motel 6",
    "SS": "Studio 6",
    "HS": "Hotel 6"
}


class Motel6Spider(scrapy.Spider):
    name = "motel6"
    allowed_domains = ["motel6.com"]
    start_urls = (
        'https://www.motel6.com/var/g6/hotel-summary/ms.infinity.1.json',
    )

    def parse(self, response):
        idata = json.loads(response.body_as_unicode())
        storeids = idata.keys()
        URL = 'https://www.motel6.com/var/g6/hotel-information/en/{}.json'
        for storeid in storeids:
            try:
                int(storeid)
            except ValueError:
                continue
            try:
                yield scrapy.Request(URL.format(storeid), callback=self.parse_hotel)
            except ValueError:
                continue

    def parse_hotel(self, response):
        mdata = json.loads(response.body_as_unicode())

        properties = {
                    'ref': mdata["property_id"],
                    'name': mdata["name"],
                    'addr_full': mdata["address"],
                    'city': mdata["city"],
                    'postcode': mdata["zip"],
                    'lat': mdata["latitude"],
                    'lon': mdata["longitude"],
                    'phone': mdata["phone"],
                    'state': mdata["state"],
                    'website': mdata["microsite_url"],
                    'brand': brand_lookup[mdata["brand_id"]],
        }

        yield GeojsonPointItem(**properties)
