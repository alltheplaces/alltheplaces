# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem


class ShopriteSpider(scrapy.Spider):
    name = "shoprite"
    item_attributes = {"brand": "ShopRite", "brand_wikidata": "Q7501097"}
    allowed_domains = ["shoprite.com"]
    start_urls = [
        "https://www.shoprite.com/",
    ]

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
                "website": f"https://www.shoprite.com/sm/planning/rsid/{ref}",
                "name": store["name"],
                "lat": store["location"]["latitude"],
                "lon": store["location"]["longitude"],
                "street_address": store["addressLine1"],
                "city": store["city"],
                "state": store["countyProvinceState"],
                "postcode": store["postCode"],
                "country": store["country"],
                "phone": store["phone"],
                "opening_hours": store["openingHours"],
            }

            yield GeojsonPointItem(**properties)
