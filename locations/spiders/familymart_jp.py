from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class FamilymartJPSpider(Spider):
    name = "familymart_jp"
    item_attributes = {"brand_wikidata": "Q11247682"}

    custom_settings = {
        "CONCURRENT_REQUESTS": 1,
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        for points in [
            "w",
            "xjb",
            "xn0",
            "xn1",
            "xn2",
            "xn3",
            "xn4",
            "xn5",
            "xn6",
            "xn70",
            "xn71",
            "xn72",
            "xn73",
            "xn74",
            "xn75",
            "xn76",
            "xn77",
            "xn78",
            "xn79",
            "xn7b",
            "xn7c",
            "xn7d",
            "xn7e",
            "xn7f",
            "xn7g",
            "xn7h",
            "xn7k",
            "xn7j",
            "xn7m",
            "xn7n",
            "xn7p",
            "xn7q",
            "xn7r",
            "xn7s",
            "xn7t",
            "xn7u",
            "xn7v",
            "xn7w",
            "xn7x",
            "xn7y",
            "xn7z",
            "xnk",
            "xn9",
            "xnd",
            "xne",
            "xns",
            "xnf",
            "xng",
            "xnu",
            "xp",
            "z",
        ]:
            yield JsonRequest(url=f"https://store.family.co.jp/api/points/{points}")

    def parse(self, response):
        for store in response.json()["items"]:

            item = DictParser.parse(store)

            match store["extra_fields"]["C1"]:
                case "1":
                    item.update({"brand_wikidata": "Q11247682"})
                    apply_category(Categories.SHOP_CONVENIENCE, item)
                case "2":
                    item.update({"brand_wikidata": "Q115868189"})
                    item.update({"brand": "ファミマ!!"})
                    apply_category(Categories.SHOP_CONVENIENCE, item)
                case "3":
                    item.update({"brand_wikidata": "Q11247682"})  # using familymart until tomony is accepted.
                    # item.update({"brand_wikidata": "Q11249798"}) # no NSI for this one yet, pull request submitted 2026-Feb-22
                    # item.update({"brand": "TOMONY"})
                    # item["extras"]["brand:en"] = "TOMONY"
                    apply_category(Categories.SHOP_CONVENIENCE, item)
                case _:
                    item.update({"brand_wikidata": "Q11247682"})
                    apply_category(Categories.SHOP_CONVENIENCE, item)

            if store["extra_fields"]["I1"] == "24時間":
                item["opening_hours"] = "24/7"
            else:
                item["opening_hours"] = store["extra_fields"]["I1"]

            item["ref"] = store["key"]
            item["website"] = f"https://store.family.co.jp/points/{store['key']}"
            item["phone"] = f"+81 {store['extra_fields']['Tel']}"
            item["postcode"] = store["extra_fields"]["ZipCode"]
            item["branch"] = store["name"]
            item["name"] = None  # resets name to brand instead of branch

            yield item
