import json

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class UsaveZASpider(scrapy.Spider):
    name = "usave_za"
    item_attributes = {"brand_wikidata": "Q1857639"}
    start_urls = [
        "https://www.usave.co.za/bin/stores.json?national=yes&brand=shoprite&country=198",
    ]

    def parse(self, response):
        for store in json.loads(response.text)["stores"]:
            store["name"] = " ".join(
                filter(
                    None,
                    [
                        store["brand"],
                        store["branch"],
                    ],
                )
            )
            store["city"] = store.pop("physicalCity")
            store["street-address"] = ", ".join(
                filter(
                    None,
                    [
                        store["physicalAdd1"],
                        store["physicalAdd2"],
                        store["physicalAdd3"],
                    ],
                )
            ).replace("null", "")
            item = DictParser.parse(store)
            item["ref"] = store["uid"]
            item["brand"] = store["brand"]
            if store["brand"] == "Shoprite" or store["brand"] == "Shoprite Hyper":
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif store["brand"] == "Shoprite LiquorShop":
                apply_category({"shop": "alcohol"}, item)
            elif store["brand"] == "Shoprite Mini":
                apply_category(Categories.SHOP_CONVENIENCE, item)
            elif store["brand"] == "Usave":
                apply_category(Categories.SHOP_CONVENIENCE, item)
                item["brand_wikidata"] = "Q115696368"
            elif store["brand"] == "MediRite" or store["brand"] == "MediRite Plus":
                apply_category(Categories.PHARMACY, item)
                item["brand_wikidata"] = "Q115696233"
            yield item
