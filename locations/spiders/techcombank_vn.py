from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.brand_utils import extract_located_in
from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.spiders.big_c_th import BigCTHSpider

LOCATED_IN_MAPPINGS = [
    (["Big C"], BigCTHSpider.item_attributes),
    (["Vinpearl"], {"brand": "Vinpearl", "brand_wikidata": "Q9094269"}),
    (["Co.opmart", "Coopmart"], {"brand": "Co.opmart", "brand_wikidata": "Q10749367"}),
]


class TechcombankVNSpider(Spider):
    name = "techcombank_vn"
    item_attributes = {"brand": "Techcombank", "brand_wikidata": "Q10541776"}

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url="https://techcombank.com/graphql/execute.json/techcombank/branchPhones",
            callback=self.parse_branches,
        )
        yield Request(
            url="https://techcombank.com/graphql/execute.json/techcombank/atmcdmSearch",
            callback=self.parse_atms,
        )

    def parse_branches(self, response, **kwargs):
        for location in response.json()["data"]["branchFragmentList"]["items"]:
            item = Feature()
            item["ref"] = location["branchId"]
            item["branch"] = location["branchNm"].removeprefix("Techcombank ")
            item["addr_full"] = location["adrLine"]["plaintext"]
            item["lat"] = location["lat"]
            item["lon"] = location["long"]
            item["phone"] = location.get("phone")
            apply_category(Categories.BANK, item)
            yield item

    def parse_atms(self, response, **kwargs):
        for location in response.json()["data"]["atmCdmFragmentList"]["items"]:
            item = Feature()
            item["ref"] = location["atmId"]
            item["name"] = location["atmName"].removeprefix("ATM ").removeprefix("CDM ")
            item["addr_full"] = location["atmAddress"]
            item["city"] = location["cityName"]
            item["state"] = location["districtName"]
            item["lat"] = location["atmLatitude"]
            item["lon"] = location["atmLongitude"]
            item["located_in"], item["located_in_wikidata"] = extract_located_in(
                location["atmName"], LOCATED_IN_MAPPINGS
            )
            apply_yes_no(Extras.CASH_IN, item, location.get("isCDM"))
            apply_category(Categories.ATM, item)
            yield item
