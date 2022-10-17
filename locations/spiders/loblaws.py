# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class LoblawsSpider(scrapy.Spider):

    name = "loblaws"
    item_attributes = {"brand": "Loblaws"}
    allowed_domains = ["www.loblaws.ca"]
    start_urls = (
        "https://www.loblaws.ca/api/pickup-locations",
    )


    def parse(self, response):
        results = response.json()
        for i in results:
            if i['locationType'] == 'STORE':
                properties = {
                    "ref": i["storeId"],
                    "name": i["name"],
                    "lat": i["geoPoint"]['latitude'],
                    "lon": i["geoPoint"]['latitude'],
                    "addr_full": i["address"]["line1"],
                    "city": i["address"]["town"],
                    "state": i["address"]["region"],
                    "postcode": i["address"]["postalCode"],
                    "country": i["address"]['country'],
                }

                yield GeojsonPointItem(**properties)
