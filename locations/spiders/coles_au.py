# -*- coding: utf-8 -*-
import re

import scrapy
import json

from locations.items import GeojsonPointItem


class ColesSpider(scrapy.Spider):
    name = "coles_au"
    item_attributes = {"brand": "Coles", "brand_wikidata": "Q1108172"}
    allowed_domains = ["apigw.coles.com.au"]
    start_urls = [
        "https://apigw.coles.com.au/digital/colesweb/v1/stores/search?latitude=-28.014547&longitude=135.171168&brandIds=2,1&numberOfStores=10",
    ]

    def parse(self, response):
        with open(
            "./locations/searchable_points/au_centroids_20km_radius.csv"
        ) as points:
            next(points)
            for point in points:
                row = point.replace("\n", "").split(",")
                lati = row[1]
                long = row[2]
                searchurl = "https://apigw.coles.com.au/digital/colesweb/v1/stores/search?latitude={la}&longitude={lo}&brandIds=2,1&numberOfStores=10".format(
                    la=lati, lo=long
                )
                yield scrapy.Request(
                    response.urljoin(searchurl), callback=self.parse_search
                )

    def parse_search(self, response):
        data = json.loads(json.dumps(response.json()))

        for i in data["stores"]:
            properties = {
                "ref": i["storeId"],
                "name": i["brandName"],
                "addr_full": i["address"],
                "city": i["suburb"],
                "state": i["state"],
                "postcode": i["postcode"],
                "country": "AU",
                "phone": i["phone"],
                "lat": i["latitude"],
                "lon": i["longitude"],
            }

            yield GeojsonPointItem(**properties)
