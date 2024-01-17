from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class TechcombankVNSpider(Spider):
    name = "techcombank_vn"
    item_attributes = {"brand": "Techcombank", "brand_wikidata": "Q10541776"}
    user_agent = BROWSER_DEFAULT

    def start_requests(self):
        yield JsonRequest(url="https://techcombank.com/api/data/apmt/list-branch", data={"serviceid": 111})

    def parse(self, response, **kwargs):
        for location in response.json()["branchList"]:
            item = Feature()
            item["ref"] = location["branchId"]
            item["name"] = location["branchNm"]
            item["addr_full"] = location["pstlAdr"]["adrLine"]
            item["lat"] = location["lat"]
            item["lon"] = location["long"]
            item["phone"] = location.get("phone")
            apply_category(Categories.BANK, item)
            yield item
