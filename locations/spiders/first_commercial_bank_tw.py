from typing import AsyncIterator, Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class FirstCommercialBankTWSpider(JSONBlobSpider):
    name = "first_commercial_bank_tw"
    item_attributes = {"brand": "第一商業銀行", "brand_wikidata": "Q11602128"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    locations_key = "branchData"

    async def start(self) -> AsyncIterator[Request]:
        url = "https://www.firstbank.com.tw/sites/REST/controller/BusinessUnitsDomesticRevCTL/searchBranch"
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        yield Request(url=url, method="POST", headers=headers, callback=self.parse)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature["branchTitle"]
        item["postcode"] = feature["branchZipcode"]
        item["city"] = feature["branchDistrict"]
        item["lat"] = feature["branchLatitude"]
        item["lon"] = feature["branchLongitude"]
        item["addr_full"] = clean_address(feature["branchAddress"])
        item["phone"] = feature["branchPhoneNo"]
        item["website"] = "".join(["https://www.firstbank.com.tw", feature["_link_"]])
        apply_category(Categories.BANK, item)
        yield item
