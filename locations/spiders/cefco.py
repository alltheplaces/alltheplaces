# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class CefcoSpider(scrapy.Spider):
    name = "cefco"
    item_attributes = {"brand": "CEFCO", "brand_wikidata": "Q110209230"}
    allowed_domains = ["cefco.com"]

    start_urls = ["https://cefcostores.com/store-locator/"]

    def parse(self, response):
        map_data = response.css("#map_data::text").get()

        for store in json.loads(map_data):
            yield GeojsonPointItem(
                ref=store["id"],
                lon=store["longitude"],
                lat=store["latitude"],
                name=store["title"],
                addr_full=store["address"],
                city=store["city"],
                state=store["state"],
                postcode=store["zip"],
                country="US",
                opening_hours="24/7" if store["hours"] == "24 Hours" else None,
                extras={
                    "amenity:fuel": store["regular"] == True or store["regular"] == "1",
                    "fuel:diesel": store["diesel"] == True or store["diesel"] == "1",
                    "fuel:HGV_diesel": store["truckstop"] == True
                    or store["truckstop"] == "1",
                    "fuel:e85": store["e85"] == True or store["e85"] == "1",
                    "fuel:octane_87": store["regular"] == True
                    or store["regular"] == "1",
                    "fuel:octane_89": store["midgrade"] == True
                    or store["midgrade"] == "1",
                    "fuel:octane_93": store["premium"] == True
                    or store["premium"] == "1",
                    "fuel:kerosene": store["kerosene"] == True
                    or store["kerosene"] == "1",
                    "car_wash": store["carwash"] == True or store["carwash"] == "1",
                    "hgv": store["truckstop"] == True or store["truckstop"] == "1",
                },
            )
