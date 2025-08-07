import json

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations


class PunjabNationalBankINSpider(scrapy.Spider):
    name = "punjab_national_bank_in"
    item_attributes = {"brand": "Punjab National Bank", "brand_wikidata": "Q2743499"}

    def start_requests(self):
        for branch_atm in ["Branch", "ATM"]:
            for city in city_locations("IN", 1500):
                yield scrapy.http.JsonRequest(
                    url="https://www.pnbindia.in/LocateUS.aspx/loadMAPDataonButton",
                    data={"searchType": branch_atm, "searchText": city["name"]},
                )

    def parse(self, response):
        data = response.json()["d"]
        if "MarkerData" in data:
            for index, store in enumerate(json.loads(data)["MarkerData"]):
                store["lon"] = store.pop("longt")
                store["address"] = store.pop("location")
                item = DictParser.parse(store)
                item["website"] = "https://www.pnbindia.in/"
                if store["loctType"] == "Branch":
                    apply_category(Categories.BANK, item)
                    item["ref"] = f'{store["IFSC"]}-{index}'
                    item["phone"] = store["Tel1"]
                else:
                    apply_category(Categories.ATM, item)
                    item["ref"] = f'{store["ATMID"]}-{index}'
                yield item
