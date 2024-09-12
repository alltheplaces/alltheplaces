import re
from copy import deepcopy

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class BnpParibasFRSpider(scrapy.Spider):
    name = "bnp_paribas_fr"
    item_attributes = {"brand": "BNP Paribas", "brand_wikidata": "Q499707"}
    start_urls = ["https://agences.mabanque.bnpparibas/engineV2/?ag=allpoi"]

    def parse(self, response):
        for code in response.json()["agence"]:
            yield scrapy.Request(
                url="https://agences.mabanque.bnpparibas/engineV2/?ag={}".format(code["code"]),
                callback=self.parsing_store_data,
            )

    def parsing_store_data(self, response):
        result = response.json()["agence"]
        item = DictParser.parse(result)
        item["name"] = result["nom"]
        item["street_address"] = result["adresse"]
        item["city"] = re.sub(r"(?i)\d+.*", "", result["ville"])
        item["postcode"] = result["cp"]
        bank = deepcopy(item)
        apply_category(Categories.BANK, bank)
        yield bank
        if result["services"]["gab"] == "1":
            item["ref"] += "-ATM"
            apply_category(Categories.ATM, item)
            yield item
