# -*- coding: utf-8 -*-
import scrapy
import json
import re
from urllib.parse import unquote

from locations.items import GeojsonPointItem


class IcelandFoodsSpider(scrapy.Spider):
    name = "iceland_foods"
    item_attributes = {"brand": "Iceland Foods"}
    allowed_domains = ["www.iceland.co.uk"]
    start_urls = ("https://www.iceland.co.uk/sitemap-store-site-map.xml",)

    # Extracts store's data from an individual store page
    def parse_store_page(self, response):
        response.selector.remove_namespaces()

        # One of the <script> tags contains a JSON object with store information
        scripts = response.css("script").xpath("./text()").getall()

        for s in scripts:
            if "LocalBusiness" in s:
                # Get a JS object with store information
                store = json.loads(s)

                # Extract store name from URL
                store_name = unquote(response.url.split("StoreName=")[1])

                # Because country is not always set in address field, guess country from name
                store_country = "Ireland" if "IRELAND " in store_name else "UK"

                store_addr = "{}, {}, {}".format(
                    store["address"]["streetAddress"],
                    store["address"]["addressRegion"],
                    store["address"]["addressLocality"],
                ).replace(", null", "")

                phone = response.css("div.phone").xpath("./text()").get()
                if phone:
                    phone.strip()

                properties = {
                    "name": store_name,
                    "ref": response.url.split("StoreID=")[1].split("&")[0],
                    "website": response.url,
                    "postcode": store["address"]["postalCode"],
                    "city": store["address"]["addressRegion"].title()
                    or "",  # Usually city, but not always
                    "addr_full": store_addr,
                    "country": store_country,
                    "phone": phone,
                }

                try:
                    properties["lat"] = float(store["geo"]["latitude"])
                    properties["lon"] = float(store["geo"]["longitude"])
                except ValueError:
                    return

                yield GeojsonPointItem(**properties)

    def parse(self, response):
        response.selector.remove_namespaces()

        for url in response.xpath("//url/loc/text()").getall():
            yield scrapy.Request(url, callback=self.parse_store_page)
