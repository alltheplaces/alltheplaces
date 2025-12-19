from typing import Any

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class HdfcBankINSpider(Spider):
    name = "hdfc_bank_in"
    item_attributes = {"brand": "HDFC Bank", "brand_wikidata": "Q631047"}
    start_urls = ["https://www.hdfc.bank.in/content/hdfcbankpws/api/city.json/content-fragments/branch-locator"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for state_data in response.json():
            for state, cities in state_data.items():
                for city in cities:
                    yield JsonRequest(
                        url=f"https://www.hdfc.bank.in/content/hdfcbankpws/api/branchlocator.{state}.{city}.json",
                        callback=self.parse_locations,
                    )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").replace("_", " ").removesuffix(" ATM")
            item["state"] = location.get("geographicalState").replace("_", " ")
            item["city"] = item["city"].replace("_", " ")
            item["addr_full"] = location.get("branchAddress")
            item["postcode"] = location.get("pincode")
            slug = location.get("pagePath").split("/branch-locator/")[-1].removesuffix(".html")
            item["website"] = f"https://www.hdfc.bank.in/branch-locator/{slug}"

            if "ATM" in location.get("type", ""):
                item["name"] = "HDFC Bank ATM"
                apply_category(Categories.ATM, item)
            else:
                apply_category(Categories.BANK, item)
            yield item
