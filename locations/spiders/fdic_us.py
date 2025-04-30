from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class FdicUSSpider(Spider):
    name = "fdic_us"
    start_urls = ["https://pfabankapi.app.cloud.gov/api/institutions?agg_by=&filters=%28ACTIVE%3A%221%22%29&limit=5000"]
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}  # , "DOWNLOAD_DELAY": 3}

    def parse(self, response):
        institutions = response.json()["data"]
        for institution in institutions:
            cert = institution["data"]["CERT"]
            branch_url = f"https://pfabankapi.app.cloud.gov/api/locations?filters=CERT:{cert}&limit=10000"
            website = institution["data"].get("WEBADDR")
            yield Request(
                branch_url,
                callback=self.parse_branches,
                cb_kwargs={"website": website},
            )

    def parse_branches(self, response, website):
        branches = response.json()["data"]
        for branch in branches:
            item = DictParser.parse(branch["data"])
            item["website"] = website
            if item["website"][0:4] != "http":
                item["website"] = f"https://{item['website']}"
            apply_category(Categories.BANK, item)

            yield item
