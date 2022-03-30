# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem


class BlueBottleCafeSpider(scrapy.Spider):

    name = "bluebottlecafe"
    item_attributes = {"brand": "Blue Bottle Cafe"}
    allowed_domains = ["www.bluebottlecoffee.com"]
    start_urls = (
        "https://bluebottlecoffee.com/api/cafe_search/fetch.json?coordinates=false&query=true&search_value=all",
    )

    def parse(self, response):
        results = response.json()
        for region_name in results["cafes"]:
            for store_data in results["cafes"][region_name]:

                address_string = (
                    store_data["address"]
                    .replace("\n", " ")
                    .replace("\r", "")
                    .replace("<br>", ", ")
                )

                properties = {
                    "name": store_data["name"],
                    "addr_full": address_string,
                    "city": address_string.split(", ")[1],
                    "website": store_data["url"],
                    "ref": store_data["id"],
                    "lon": store_data["longitude"],
                    "lat": store_data["latitude"],
                }

                yield GeojsonPointItem(**properties)
