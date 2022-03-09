# -*- coding: utf-8 -*-
import scrapy
import json
import re
from urllib.parse import unquote

from locations.items import GeojsonPointItem


class TheRangeSpider(scrapy.Spider):
    name = "therange"
    item_attributes = {"brand": "The Range"}
    allowed_domains = ["www.therange.co.uk"]
    start_urls = ("https://www.therange.co.uk/stores/",)

    # Stores catalog has a JS array with store coordinates
    store_to_geo = {}

    # Extracts store's data from an individual store page
    def parse_store_page(self, response):
        response.selector.remove_namespaces()

        # One of the <script> tags contains a JSON object with store information
        scripts = response.css("script").xpath("./text()").getall()

        for s in scripts:
            if "Store" in s and "schema.org" in s:

                try:
                    # Get a JS object with store information
                    store = json.loads(s)

                    properties = {
                        "name": store["name"],
                        "ref": store["name"],
                        "website": response.url,
                        "postcode": store["address"]["postalCode"],
                        "city": store["address"]["addressLocality"],
                        "country": store["address"]["addressCountry"],
                        "street": store["address"]["streetAddress"],
                        "phone": store["telephone"],
                        "lat": self.store_to_geo[store["name"].split(":")[1].strip()][
                            0
                        ],
                        "lon": self.store_to_geo[store["name"].split(":")[1].strip()][
                            1
                        ],
                    }

                    yield GeojsonPointItem(**properties)

                except:
                    return

    def parse(self, response):
        response.selector.remove_namespaces()

        # Create a crosswalk dictionary { "Store": [lat, lon], ... } from JS
        scripts = response.css("script").xpath("./text()").getall()

        for s in scripts:
            if "initStoreFinder()" in s:

                # Extract markers array as a string
                markers_str = s.split("var markers = [")[1].split("];")[0].strip()

                # Turn the string into a list of individual store strings "Store,Lat,Lon"
                markers = (
                    markers_str.replace("[", "").replace("\n", "").split("],")[:-1]
                )

                # Save data into store_to_geo class variable
                for marker in markers:
                    self.store_to_geo[marker.split(",")[0][1:-1]] = [
                        float(marker.split(",")[1]),
                        float(marker.split(",")[2]),
                    ]

        for store in response.css("#storelist li a::attr(href)").getall():
            yield scrapy.Request(
                response.urljoin(store), callback=self.parse_store_page
            )
