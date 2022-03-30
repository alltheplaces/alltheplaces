# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class LidlUSSpider(scrapy.Spider):
    name = "lidl_us"
    item_attributes = {"brand": "Lidl", "brand_wikidata": "Q151954"}
    allowed_domains = ["lidl.com"]
    start_urls = [
        "https://mobileapi.lidl.com/v1/stores",
    ]

    def parse(self, response):
        data = response.json()

        for store in data["results"]:
            properties = {
                "name": store["name"],
                "ref": store["crmStoreID"],
                "addr_full": store["address"]["street"],
                "city": store["address"]["city"],
                "state": store["address"]["state"],
                "postcode": store["address"]["zip"],
                "country": store["address"]["country"],
                "phone": store["phone"],
                "lat": float(store["coordinates"]["lat"]),
                "lon": float(store["coordinates"]["lon"]),
            }

            yield GeojsonPointItem(**properties)
