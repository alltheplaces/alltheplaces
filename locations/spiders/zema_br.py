import re

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class ZemaBRSpider(scrapy.Spider):
    name = "zema_br"
    item_attributes = {"brand": "Zema", "brand_wikidata": "Q123166034"}
    start_urls = [
        "https://a1594069c1prd-admin.occa.ocs.oraclecloud.com/ccstorex/custom/api/v1/storeLocations/all-locations"
    ]

    def parse(self, response, **kwargs):
        for store in response.json()["return"]["locations"]:
            store["latitude"], store["longitude"] = [
                re.sub(r"(-?\d\d)(\d+)", r"\1.\2", coord) if "." not in coord else coord
                for coord in [str(store["latitude"]), str(store["longitude"])]
            ]
            item = DictParser.parse(store)
            item["branch"] = item.pop("name").replace("Zema Loja Eletro - ", "").split("-")[1].strip()
            item["ref"] = store.get("externalLocationId")
            item["state"] = store.get("stateAddress")
            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
            yield item
