# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem


class HoneyBakedHamSpider(scrapy.Spider):
    # download_delay = 0.2
    name = "honey_baked"
    item_attributes = {"brand": "Honey Baked Ham", "brand_wikidata": "Q5893363"}
    allowed_domains = ["honeybaked.com"]
    start_urls = ("https://www.honeybaked.com/stores",)

    def parse(self, response):
        with open(
            "./locations/searchable_points/us_centroids_25mile_radius.csv"
        ) as points:
            next(points)
            for point in points:
                row = point.replace("\n", "").split(",")
                lati = row[1]
                long = row[2]
                searchurl = "https://www.honeybaked.com/api/store/v1/?long={lo}&lat={la}&radius=25".format(
                    la=lati, lo=long
                )
                yield scrapy.Request(
                    response.urljoin(searchurl), callback=self.parse_search
                )

    def parse_search(self, response):
        data = response.json()

        for i in data:

            properties = {
                "ref": i["storeInformation"]["storeId"],
                "name": i["storeInformation"]["displayName"],
                "addr_full": i["storeInformation"]["address1"],
                "city": i["storeInformation"]["city"],
                "state": i["storeInformation"]["state"],
                "postcode": i["storeInformation"]["zipCode"],
                "country": i["storeInformation"]["countryCode"],
                "phone": i["storeInformation"]["phoneNumber"],
                "lat": float(i["storeInformation"]["location"]["coordinates"][1]),
                "lon": float(i["storeInformation"]["location"]["coordinates"][0]),
            }
            yield GeojsonPointItem(**properties)
