# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem


class PriceRiteSpider(scrapy.Spider):
    name = "pricerite"
    item_attributes = {"brand": "PriceRite", "brand_wikidata": "Q7242560"}
    allowed_domains = ["priceritemarketplace.com"]

    start_urls = ("https://www.priceritemarketplace.com/",)

    def parse(self, response):
        script = response.xpath(
            '//script[contains(text(), "__PRELOADED_STATE__")]/text()'
        ).extract_first()
        script = script[script.index("{") :]
        stores = json.loads(script)["stores"]["availablePlanningStores"]["items"]

        for store in stores:
            ref = store["retailerStoreId"]
            properties = {
                "ref": ref,
                "website": f"https://www.priceritemarketplace.com/sm/planning/rsid/{ref}",
                "name": store["name"],
                "lat": store["location"]["latitude"],
                "lon": store["location"]["longitude"],
                "addr_full": store["addressLine1"],
                "city": store["city"],
                "state": store["countyProvinceState"],
                "postcode": store["postCode"],
                "phone": store["phone"],
                "opening_hours": store["openingHours"],
            }

            yield GeojsonPointItem(**properties)
