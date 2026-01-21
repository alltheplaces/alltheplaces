import json

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class KrakowskiBankSpoldzielczyPLSpider(scrapy.Spider):
    name = "krakowski_bank_spoldzielczy_pl"
    item_attributes = {"brand": "Krakowski Bank Spółdzielczy", "brand_wikidata": "Q11747876"}
    start_urls = ["https://www.kbsbank.com.pl/oddzialy", "https://www.kbsbank.com.pl/bankomaty"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        if "oddzialy" in response.url:
            data = response.xpath("//*[@data-all-departments]/@data-all-departments").get()
            for bank in json.loads(data):
                item = DictParser.parse(bank)
                item["branch"] = item.pop("name")
                apply_category(Categories.BANK, item)
                yield item
        elif "bankomaty" in response.url:
            data = response.xpath("//*[@data-locations]/@data-locations").get()
            for atm in json.loads(data):
                if atm.get("operator") == "KBS":
                    item = DictParser.parse(atm)
                    item["name"] = None
                    apply_category(Categories.ATM, item)
                    yield item
