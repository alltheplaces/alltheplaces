import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class KrakowskiBankSpoldzielczyPLSpider(scrapy.Spider):
    name = "krakowski_bank_spoldzielczy_pl"
    item_attributes = {"brand": "Krakowski Bank Spółdzielczy", "brand_wikidata": "Q11747876"}
    start_urls = ["https://www.kbsbank.com.pl/data/department", "https://www.kbsbank.com.pl/data/atm"]

    def parse(self, response, **kwargs):
        if "department" in response.url:
            for bank in response.json():
                item = DictParser.parse(bank)
                item["branch"] = item.pop("name")
                apply_category(Categories.BANK, item)
                yield item
        elif "atm" in response.url:
            for bank in response.json():
                if bank["operator"] == "KBS":
                    item = DictParser.parse(bank)
                    item["name"] = None
                    apply_category(Categories.ATM, item)
                    yield item
