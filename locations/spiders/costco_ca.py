from typing import Any, Iterable

import scrapy
from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class CostcoCASpider(scrapy.Spider):
    name = "costco_ca"
    item_attributes = {"name": "Costco", "brand": "Costco", "brand_wikidata": "Q715583"}
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def start_requests(self) -> Iterable[Request]:
        yield scrapy.Request(
            url="https://www.costco.ca/AjaxWarehouseBrowseLookupView?countryCode=CA", callback=self.parse
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            if isinstance(store, dict):
                item = DictParser.parse(store)
                item.pop("name")
                item["ref"] = store["stlocID"]
                item["branch"] = store["locationName"]
                item["website"] = (
                    "https://www.costco.ca/warehouse-locations/"
                    + "-".join([item["branch"].replace(" ", "-"), item["state"], str(item["ref"])])
                    + ".html"
                )
                apply_category(Categories.SHOP_WHOLESALE, item)
                yield item
