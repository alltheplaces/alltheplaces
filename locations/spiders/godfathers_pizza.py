# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class GodfathersPizzaSpider(scrapy.Spider):
    name = "godfathers_pizza"
    item_attributes = {"brand": "Godfather's Pizza", "brand_wikidata": "Q5576353"}
    allowed_domains = ["tillster.com"]
    start_urls = [
        "https://api-prod-gfp-us-a.tillster.com/mobilem8-web-service/rest/storeinfo/distance?_=1601656666666&\
        disposition=DINE_IN,PICKUP,DELIVERY&latitude=39.0213953&longitude=-94.3116155&maxResults=2000&radius=5000&\
        statuses=ACTIVE,TEMP-INACTIVE,ORDERING-DISABLED&tenant=gfp-us",
    ]

    def parse(self, response):
        stores = response.json()

        for store in stores["getStoresResult"]["stores"]:
            properties = {
                "ref": store["storeName"],
                "name": store["storeName"],
                "addr_full": store["street"],
                "city": store["city"],
                "state": store["state"],
                "postcode": store["zipCode"],
                "country": "US",
                "lat": store["latitude"],
                "lon": store["longitude"],
                "phone": store["phoneNumber"],
            }

            yield GeojsonPointItem(**properties)
