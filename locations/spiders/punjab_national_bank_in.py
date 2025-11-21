from json import loads
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations


class PunjabNationalBankINSpider(Spider):
    name = "punjab_national_bank_in"
    item_attributes = {"brand": "Punjab National Bank", "brand_wikidata": "Q2743499"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for branch_atm in ["Branch", "ATM"]:
            for city in city_locations("IN", 1500):
                yield JsonRequest(
                    url="https://www.pnbindia.in/LocateUS.aspx/loadMAPDataonButton",
                    data={"searchType": branch_atm, "searchText": city["name"]},
                )

    def parse(self, response):
        data = response.json()["d"]
        if "MarkerData" in data:
            for index, store in enumerate(loads(data)["MarkerData"]):
                store["lon"] = store.pop("longt")
                store["address"] = store.pop("location")
                item = DictParser.parse(store)
                if store["loctType"] == "Branch":
                    apply_category(Categories.BANK, item)
                    item["ref"] = f'{store["IFSC"]}-{index}'
                    item["phone"] = store["Tel1"]
                else:
                    apply_category(Categories.ATM, item)
                    item["ref"] = f'{store["ATMID"]}-{index}'
                yield item
