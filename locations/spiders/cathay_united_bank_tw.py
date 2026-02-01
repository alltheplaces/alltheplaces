from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.brand_utils import extract_located_in
from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.carrefour_tw import CarrefourTWSpider
from locations.spiders.costco_au import COSTCO_SHARED_ATTRIBUTES
from locations.spiders.familymart_tw import FamilymartTWSpider
from locations.spiders.pxmart_tw import PxmartTWSpider
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES


class CathayUnitedBankTWSpider(Spider):
    name = "cathay_united_bank_tw"
    item_attributes = {"brand": "國泰世華商業銀行", "brand_wikidata": "Q702656"}

    LOCATED_IN_MAPPINGS = [
        (["FAMILYMART", "FAMILY"], FamilymartTWSpider.item_attributes),
        (["7-ELEVEN", "7-11"], SEVEN_ELEVEN_SHARED_ATTRIBUTES),
        (["HI-LIFE", "HILIFE"], {"brand": "Hi-Life", "brand_wikidata": "Q11326216"}),
        (["OK MART"], {"brand": "OK Mart", "brand_wikidata": "Q10851968"}),
        (["PX MART"], PxmartTWSpider.item_attributes),
        (["CARREFOUR"], CarrefourTWSpider.brands["量販"]),
        (["RT-MART"], {"brand": "RT-Mart", "brand_wikidata": "Q7277802"}),
        (["WELLCOME"], {"brand": "Wellcome", "brand_wikidata": "Q706247"}),
        (["COSTCO"], COSTCO_SHARED_ATTRIBUTES),
    ]

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
                        # Extract retail brand from SetAddressKind field for ATMs
                        item["located_in"], item["located_in_wikidata"] = extract_located_in(
                            details.get("SetAddressKind", ""), self.LOCATED_IN_MAPPINGS, self
                        )
                    yield item
