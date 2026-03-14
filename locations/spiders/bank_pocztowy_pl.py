import re

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class BankPocztowyPLSpider(scrapy.Spider):
    name = "bank_pocztowy_pl"
    item_attributes = {"brand": "Bank Pocztowy", "brand_wikidata": "Q4034834"}
    start_urls = ["https://www.pocztowy.pl/vars/map_p.json", "https://www.pocztowy.pl/vars/map_b.json"]
    no_refs = True

    def parse(self, response, **kwargs):
        if "map_p.json" in response.url:
            for bank in response.json():
                item = DictParser.parse(bank)
                item["street_address"] = bank["adr"]
                item["lat"], item["lon"] = re.search(r"(\d+\.\d+),(\d+\.\d+)", bank["gmap"]).groups()
                apply_category(Categories.BANK, item)

                yield item
        elif "map_b.json" in response.url:
            for atm in response.json():
                if "PKOBP" in atm["name"]:
                    item = DictParser.parse(atm)
                    item["street_address"] = atm["adr"]
                    item["lat"], item["lon"] = re.search(r"(\d+\.\d+),(\d+\.\d+)", atm["gmap"]).groups()
                    apply_category(Categories.ATM, item)
                    yield item
