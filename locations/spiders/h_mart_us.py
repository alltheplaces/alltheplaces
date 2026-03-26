from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class HMartUSSpider(Spider):
    name = "h_mart_us"
    item_attributes = {"brand": "H Mart", "brand_wikidata": "Q5636306"}

    async def start(self):
        yield JsonRequest(
            "https://www.hmart.com/_v/private/graphql/v1?workspace=master&maxAge=long&appsEtag=remove&domain=store&locale=en-US&__bindingId=0b48cd1a-951b-4fa9-8472-2b68ae904016",
            data={
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
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        stores = response.json()["data"]["getStores"]["items"]
        for store in stores:
            if store["isActive"] is not True:
                continue
            store["address"]["street_address"] = store["address"].pop("street")
            item = DictParser.parse(store)
            item["lat"] = store["address"]["location"]["latitude"]
            item["lon"] = store["address"]["location"]["longitude"]
            item["housenumber"] = store["address"]["number"]
            item["branch"] = item.pop("name")
            item["phone"] = store["instructions"]
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
