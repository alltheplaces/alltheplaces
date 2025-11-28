from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class CathayUnitedBankTWSpider(Spider):
    name = "cathay_united_bank_tw"
    item_attributes = {"brand": "國泰世華商業銀行", "brand_wikidata": "Q702656"}

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url="https://www.cathaybk.com.tw/CathayBK/service/Locations/LocationsGetEnData.ashx", callback=self.parse
        )

    def parse(self, response, **kwargs):
        for branch_type in ["Branch", "Atm"]:
            for key, value in response.json()[f"{branch_type}"].items():
                if key == "All" and value:
                    continue
                for details in value:
                    item = DictParser.parse(details)
                    item["city"] = key
                    item["website"] = "https://www.cathaybk.com.tw/"
                    if branch_type == "Branch":
                        item["branch"] = details["BranchName"]
                        item["ref"] = "-".join([details["BranchID"], "BRANCH"])
                        item["phone"] = details["TelNo"]
                        apply_category(Categories.BANK, item)
                    elif branch_type == "Atm":
                        item["name"] = "-".join(["國泰世華商業銀行", "ATM"])
                        item["ref"] = "-".join([details["Sno"], "ATM"])
                        item["street"] = details["SetAddressKind"]
                        apply_category(Categories.ATM, item)
                    yield item
