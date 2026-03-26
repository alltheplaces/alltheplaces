import json

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class HMartUSSpider(scrapy.Spider):
    name = "h_mart_us"
    item_attributes = {"brand": "H Mart", "brand_wikidata": "Q5636306"}

    async def start(self):
        url = "https://www.hmart.com/_v/private/graphql/v1?workspace=master&maxAge=long&appsEtag=remove&domain=store&locale=en-US&__bindingId=0b48cd1a-951b-4fa9-8472-2b68ae904016"

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://www.hmart.com",
            "Referer": "https://www.hmart.com/storelocator",
            "User-Agent": "Mozilla/5.0",
            "x-vtex-use-https": "true",
        }

        payload = {
            "operationName": "getStores",
            "variables": {},
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "d126e9e1e4aeaf939fd9cb010881f0a4f78a2394008821968eb8422f78238668",
                    "sender": "hmartus.store-locator@1.x",
                    "provider": "hmartus.store-locator@1.x",
                }
            },
        }

        yield scrapy.Request(url=url, method="POST", headers=headers, body=json.dumps(payload), callback=self.parse)

    def parse(self, response):
        stores = response.json()["data"]["getStores"]["items"]
        for store in stores:
            if store["isActive"] is not True:
                continue
            store["address"]["street_address"] = store["address"].pop("street")
            item = DictParser.parse(store)
            item.update(DictParser.parse(store["address"]))
            item["housenumber"] = store["address"]["number"]
            item["branch"] = store["name"]
            item["phone"] = store["instructions"]
            item["ref"] = store["id"]
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
