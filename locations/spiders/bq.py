# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class BQSpider(scrapy.Spider):
    name = "bq"
    item_attributes = {"brand": "B&Q"}
    allowed_domains = ["www.diy.com"]
    # To get a new atmosphere_app_id key, check Network calls within https://www.diy.com/find-a-store/ (call to api.kingfisher.com)
    start_urls = (
        "https://api.kingfisher.com/v1/mobile/stores/BQUK?nearLatLong=51.515617%2C-0.091998&page[size]=500&atmosphere_app_id=kingfisher-7c4QgmLEROp4PUh0oUebbI94",
    )

    def parse(self, response):
        response.selector.remove_namespaces()

        data = json.loads(response.xpath("//text()").get())["data"]

        for store in data:
            if store["type"] == "store":
                try:

                    country = store["attributes"]["store"]["geoCoordinates"]["country"]
                    country = "Ireland" if country == "Eire" else country

                    properties = {
                        "name": store["attributes"]["store"]["name"],
                        "ref": store["id"],
                        "website": "https://www.diy.com{}".format(
                            store["attributes"]["seoPath"]
                        ),
                        "postcode": store["attributes"]["store"]["geoCoordinates"][
                            "postalCode"
                        ],
                        "city": store["attributes"]["store"]["geoCoordinates"][
                            "address"
                        ]["lines"][-2],
                        "country": country,
                        "addr_full": store["attributes"]["store"]["geoCoordinates"][
                            "address"
                        ]["lines"][0],
                        "phone": store["attributes"]["store"]["contactPoint"][
                            "telephone"
                        ],
                        "lat": float(
                            store["attributes"]["store"]["geoCoordinates"]["latitude"]
                        ),
                        "lon": float(
                            store["attributes"]["store"]["geoCoordinates"]["longitude"]
                        ),
                    }

                    yield GeojsonPointItem(**properties)

                except:
                    break
