# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class KiplingSpider(scrapy.Spider):
    name = "kipling"
    item_attributes = {"brand": "Kipling"}
    allowed_domains = ["kipling-usa.com"]
    start_urls = (
        "https://www.kipling-usa.com/on/demandware.store/Sites-kip-Site/default/Stores-GetNearestStores?countryCode=US&onlyCountry=true",
    )

    def parse(self, response):
        data = response.json()

        for store in data:
            if (
                data[store]["department"] == "Outlet Store"
                or data[store]["department"] == "Retail Store"
            ):
                properties = {
                    "ref": data[store]["storeID"],
                    "name": data[store]["name"],
                    "addr_full": data[store]["address1"],
                    "city": data[store]["city"],
                    "state": data[store]["stateCode"],
                    "postcode": data[store]["postalCode"],
                    "country": data[store]["countryCode"],
                    "lat": data[store]["latitude"],
                    "lon": data[store]["longitude"],
                    "phone": data[store]["phone"],
                }

                yield GeojsonPointItem(**properties)
