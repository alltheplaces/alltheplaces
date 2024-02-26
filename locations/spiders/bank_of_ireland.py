import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class BankOfIrelandSpider(Spider):
    name = "bank_of_ireland"
    item_attributes = {"brand": "Bank of Ireland", "brand_wikidata": "Q806689"}
    start_urls = ["https://www.bankofireland.com/branch-locator/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = json.loads(re.search(r"window.DATA_INIT = ({.+});", response.text).group(1))
        for location in data["branches"].values():
            item = Feature()
            item["lat"] = location["position"]["lat"]
            item["lon"] = location["position"]["lng"]
            item["ref"] = item["website"] = "https://www.bankofireland.com/branch-locator/{}/".format(location["slug"])
            item["branch"] = location["name"]
            item["addr_full"] = location["address"]

            apply_category(Categories.BANK, item)

            yield item
        for location in data["atms"].values():
            item = Feature()
            item["lat"] = location["position"]["lat"]
            item["lon"] = location["position"]["lng"]
            item["ref"] = location["id"]
            item["branch"] = location["name"]
            item["addr_full"] = location["address"]

            apply_category(Categories.ATM, item)

            yield item
