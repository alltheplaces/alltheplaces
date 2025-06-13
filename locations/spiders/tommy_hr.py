from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class TommyHRSpider(Spider):
    name = "tommy_hr"
    item_attributes = {"brand": "Tommy", "brand_wikidata": "Q12643718"}

    def start_requests(self):
        yield JsonRequest(url="https://spiza.tommy.hr/api/v2/shop/channels?itemsPerPage=500")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["hydra:member"]:
            item = DictParser.parse(store["location"])
            item["branch"] = (
                item.pop("name")
                .removeprefix("Tommy ")
                .removeprefix("Hipermarket ")
                .removeprefix("Supermarket ")
                .removeprefix("supermarket ")
                .removeprefix("Market ")
                .removeprefix("Maximarket ")
                .removeprefix("maximarket ")
            )
            item["ref"] = store["storeCode"]
            item["lat"] = store["position"]["latitude"]
            item["lon"] = store["position"]["longitude"]
            item["state"] = store["location"]["provinceName"]
            if store["storeType"] == "Market":
                apply_category(Categories.SHOP_CONVENIENCE, item)
            else:
                apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
