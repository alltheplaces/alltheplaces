from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class BankLeumiILSpider(Spider):
    name = "bank_leumi_il"
    allowed_domains = ["www.leumi.co.il"]
    item_attributes = {"brand_wikidata": "Q806641"}
    start_urls = ["https://www.leumi.co.il/leumi_main/branches"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for id, poi in response.json()["branches"].items():
            item = DictParser.parse(poi)
            item["ref"] = id
            item["street_address"] = item.pop("addr_full")
            item["phone"] = None
            item["lat"], item["lon"] = poi["coords"]["lat"], poi["coords"]["lng"]
            if poi["type"] == "5":
                # Digital office - an ATM
                apply_category(Categories.ATM, item)
                yield item
            elif poi["type"] == "0":
                # Normal offices
                apply_yes_no(Extras.ATM, item, poi.get("atm"))
                apply_category(Categories.BANK, item)
                # TODO: Add opening hours
                yield item
