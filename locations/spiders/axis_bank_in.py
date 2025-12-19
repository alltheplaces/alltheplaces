from typing import AsyncIterator

from scrapy.http import JsonRequest
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class AxisBankINSpider(Spider):
    name = "axis_bank_in"
    item_attributes = {"brand": "Axis Bank", "brand_wikidata": "Q2003549"}
    start_urls = ["https://branch.axisbank.com/"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://j617xjxwjd.execute-api.ap-south-1.amazonaws.com/axis_bank_prod/getCmsData-V18",
            data={
                "functionName": "getHomePageData",
                "searchType": "Advanced",
                "location": "",
                "cityAdvanceSearch": "",
                "state": "",
                "outletType": "Both",
            },
            callback=self.parse,
        )

    def parse(self, response, **kwargs):
        for state in response.json()["state"]:
            yield JsonRequest(
                url="https://j617xjxwjd.execute-api.ap-south-1.amazonaws.com/axis_bank_prod/getCmsData-V18",
                data={
                    "functionName": "getHomeSearchResultElastic",
                    "city": "",
                    "searchType": "Advanced",
                    "state": f"{state}",
                    "cityAdvanceSearch": "",
                    "location": "",
                    "radius": "",
                    "outletType": "Both",
                    "searchCategory": [],
                    "searchService": [],
                    "search": "",
                    "offSet": "0",
                    "pagesize": "2000",
                },
                callback=self.parse_details,
            )

    def parse_details(self, response):
        for location in response.json()["dealerData"]:
            location["latitude"] = location["latitude"].replace(", ", "")
            item = DictParser.parse(location)
            item["addr_full"] = location["complete_address"]
            item["branch"] = location["dealerName"].removeprefix("Axis Bank Branch ")
            item["website"] = "/".join(["https://branch.axisbank.com", location["seoSlug"], "Home"])
            item["postcode"] = location["pin_code"]
            item["opening_hours"] = OpeningHours()
            if location["openHr"] == "Open 24 hours":
                item["opening_hours"] = "24/7"
            else:
                item["opening_hours"].add_ranges_from_string(location["openHr"].replace("|", "-"))
            if location["category"] == "Branch":
                apply_category(Categories.BANK, item)
            else:
                apply_category(Categories.ATM, item)
            yield item
