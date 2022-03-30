# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class ShopriteSpider(scrapy.Spider):
    name = "shoprite"
    item_attributes = {"brand": "ShopRite"}
    allowed_domains = ["shoprite.com"]

    def start_requests(self):
        url = "https://shoprite.com/StoreLocatorSearch"

        for region in ["CT", "DE", "MD", "PA", "NJ", "NY"]:
            payload = {
                "Region": region,
                "City": "",
                "SearchTerm": "",
                "FilterOptions%5B0%5D.IsActive": "false",
                "FilterOptions%5B0%5D.Name": "Online%20Grocery%20Delivery",
                "FilterOptions%5B0%5D.Value": "MwgService%3AShop2GroDelivery",
                "FilterOptions%5B1%5D.IsActive": "false",
                "FilterOptions%5B1%5D.Name": "Online%20Grocery%20Pickup",
                "FilterOptions%5B1%5D.Value": "MwgService%3AShop2GroPickup",
                "FilterOptions%5B2%5D.IsActive": "false",
                "FilterOptions%5B2%5D.Name": "Platters%2C%20Cakes%20%26%20Catering",
                "FilterOptions%5B2%5D.Value": "MwgService%3AOrderReady",
                "FilterOptions%5B3%5D.IsActive": "false",
                "FilterOptions%5B3%5D.Name": "Pharmacy",
                "FilterOptions%5B3%5D.Value": "MwgService%3AUmaPharmacy",
                "FilterOptions%5B4%5D.IsActive": "false",
                "FilterOptions%5B4%5D.Name": "Retail%20Dietitian",
                "FilterOptions%5B4%5D.Value": "ShoppingService%3ARetail%20Dietitian",
                "Radius": "150",
                "Take": "999",
            }

            yield scrapy.FormRequest(url=url, formdata=payload)

    def parse(self, response):
        stores = json.loads(re.search(r"stores: (\[{.*}\])", response.text).groups()[0])
        for store in stores:
            store_id = store["PseudoStoreId"]
            addr_1 = response.xpath(
                '//li[@id="{}"]//div[@class="store__address"]/div[1]/text()'.format(
                    store_id
                )
            ).extract_first()
            city_state_post = response.xpath(
                '//li[@id="{}"]//div[@class="store__address"]/div[2]/text()'.format(
                    store_id
                )
            ).extract_first()
            city, state, post = re.search(
                r"(.*?), (.*?) (\d+)", city_state_post
            ).groups()

            properties = {
                "ref": store_id,
                "name": store["StoreName"],
                "lat": store["Coordinates"]["Latitude"],
                "lon": store["Coordinates"]["Longitude"],
                "addr_full": addr_1.strip(),
                "city": city,
                "state": state,
                "postcode": post,
                "website": "https://shoprite.com/store/" + store_id,
            }

            yield GeojsonPointItem(**properties)
