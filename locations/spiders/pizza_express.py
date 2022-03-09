# -*- coding: utf-8 -*-
import re

import scrapy
import json

from locations.items import GeojsonPointItem


class PizzaExpressSpider(scrapy.Spider):
    # download_delay = 0.2
    name = "pizza_express"
    item_attributes = {"brand": "Pizza Express", "brand_wikidata": "Q662845"}
    allowed_domains = ["pizzaexpress.com"]
    start_urls = ("https://www.pizzaexpress.com/",)

    def parse(self, response):
        with open(
            "./locations/searchable_points/eu_centroids_120km_radius_country.csv"
        ) as points:
            next(points)
            for point in points:
                row = point.replace("\n", "").split(",")
                lati = row[1]
                long = row[2]
                country = row[3]
                if country == "UK":
                    searchurl = "https://www.pizzaexpress.com/api/Restaurants/FindRestaurantsByLatLong?latitude={la}&longitude={lo}&searchTerm=246%20Bradford%20Street%2C%20Birmingham%2C%20UK&pageNumber=1&limit=2000".format(
                        la=lati, lo=long
                    )
                    yield scrapy.Request(
                        response.urljoin(searchurl), callback=self.parse_search
                    )

    def parse_search(self, response):
        data = json.loads(json.dumps(response.json()))

        for i in data:
            if i["fullAddress"] != "":
                if i["Location"] != "":

                    properties = {
                        "ref": i["restaurantId"],
                        "name": "Pizza Express",
                        "addr_full": i["fullAddress"].split(", ")[0],
                        "city": i["Location"],
                        "postcode": i["Postcode"],
                        "country": "UK",
                        "phone": i["phone"],
                        "lat": float(i["latitude"]),
                        "lon": float(i["longitude"]),
                    }
                    yield GeojsonPointItem(**properties)
                else:
                    properties = {
                        "ref": i["restaurantId"],
                        "name": "Pizza Express",
                        "addr_full": i["fullAddress"].split(", ")[0],
                        "city": i["fullAddress"].split(", ")[-2],
                        "postcode": i["Postcode"],
                        "country": "UK",
                        "phone": i["phone"],
                        "lat": float(i["latitude"]),
                        "lon": float(i["longitude"]),
                    }
                    yield GeojsonPointItem(**properties)
            else:
                pass
