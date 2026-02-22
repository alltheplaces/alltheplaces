from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class FamilymartJPSpider(Spider):
    name = "familymart_jp"
    item_attributes = {
        "brand": "ファミリーマート",
        "brand_wikidata": "Q11247682",
        "extras": Categories.SHOP_CONVENIENCE.value,
    }

    start_urls = [
        "https://store.family.co.jp/api/points/w",
        "https://store.family.co.jp/api/points/xjb",
        "https://store.family.co.jp/api/points/xn0",
        "https://store.family.co.jp/api/points/xn1",
        "https://store.family.co.jp/api/points/xn2",
        "https://store.family.co.jp/api/points/xn3",
        "https://store.family.co.jp/api/points/xn4",
        "https://store.family.co.jp/api/points/xn5",
        "https://store.family.co.jp/api/points/xn6",
        "https://store.family.co.jp/api/points/xn70",
        "https://store.family.co.jp/api/points/xn71",
        "https://store.family.co.jp/api/points/xn72",
        "https://store.family.co.jp/api/points/xn73",
        "https://store.family.co.jp/api/points/xn74",
        "https://store.family.co.jp/api/points/xn75",
        "https://store.family.co.jp/api/points/xn76",
        "https://store.family.co.jp/api/points/xn77",
        "https://store.family.co.jp/api/points/xn78",
        "https://store.family.co.jp/api/points/xn79",
        "https://store.family.co.jp/api/points/xn7b",
        "https://store.family.co.jp/api/points/xn7c",
        "https://store.family.co.jp/api/points/xn7d",
        "https://store.family.co.jp/api/points/xn7e",
        "https://store.family.co.jp/api/points/xn7f",
        "https://store.family.co.jp/api/points/xn7g",
        "https://store.family.co.jp/api/points/xn7h",
        "https://store.family.co.jp/api/points/xn7k",
        "https://store.family.co.jp/api/points/xn7j",
        "https://store.family.co.jp/api/points/xn7m",
        "https://store.family.co.jp/api/points/xn7n",
        "https://store.family.co.jp/api/points/xn7p",
        "https://store.family.co.jp/api/points/xn7q",
        "https://store.family.co.jp/api/points/xn7r",
        "https://store.family.co.jp/api/points/xn7s",
        "https://store.family.co.jp/api/points/xn7t",
        "https://store.family.co.jp/api/points/xn7u",
        "https://store.family.co.jp/api/points/xn7v",
        "https://store.family.co.jp/api/points/xn7w",
        "https://store.family.co.jp/api/points/xn7x",
        "https://store.family.co.jp/api/points/xn7y",
        "https://store.family.co.jp/api/points/xn7z",
        "https://store.family.co.jp/api/points/xnk",
        "https://store.family.co.jp/api/points/xn9",
        "https://store.family.co.jp/api/points/xnd",
        "https://store.family.co.jp/api/points/xne",
        "https://store.family.co.jp/api/points/xns",
        "https://store.family.co.jp/api/points/xnf",
        "https://store.family.co.jp/api/points/xng",
        "https://store.family.co.jp/api/points/xnu",
        "https://store.family.co.jp/api/points/xp",
        "https://store.family.co.jp/api/points/z",
    ]

    allowed_domains = ["store.family.co.jp"]
    country_code = "JP"

    def parse(self, response: Response, **kwargs: Any) -> Any:
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

            yield item
