import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class MiddysAUSpider(scrapy.Spider):
    name = "middys_au"
    item_attributes = {"brand": "Middy's", "brand_wikidata": "Q117157352"}
    start_urls = ["https://www.middys.com.au/branch-locator"]
    custom_settings = {
        "COOKIES_ENABLED": True,
    }

    def parse(self, response, **kwargs):
        token = response.xpath('//*[contains(@name,"__RequestVerificationToken")]/@value').get()
        url = "https://www.middys.com.au/api/BranchLocator/GetBranchListForAllStateWithPromoBanner?latitude=-23.97057132215995&longitude=133.59246919154913&state="
        headers = {
            "RequestVerificationToken": token,
        }
        yield JsonRequest(url=url, headers=headers, callback=self.parse_details)

    def parse_details(self, response):
        for store in response.json()["searchBranches"]:
            item = DictParser.parse(store)
            item["website"] = "/".join(
                [
                    "https://www.middys.com.au/branch-locator",
                    item["state"],
                    item["name"].replace(" ", "-").replace("(", "").replace(")", ""),
                ]
            )
            item["street_address"] = store["branchAddress"]
            yield item
