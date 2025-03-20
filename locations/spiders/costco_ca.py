from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class CostcoCASpider(Spider):
    name = "costco_ca"
    item_attributes = {"brand": "Costco", "brand_wikidata": "Q715583"}
    start_urls = ["https://www.costco.ca/AjaxWarehouseBrowseLookupView?countryCode=CA"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            if not isinstance(store, dict):
                continue
            item = DictParser.parse(store)
            item["ref"] = item.pop("name")
            item["branch"] = store["locationName"]
            item["website"] = (
                "https://www.costco.ca/warehouse-locations/"
                + "-".join([item["branch"].replace(" ", "-"), item["state"], str(item["ref"])])
                + ".html"
            )
            apply_category(Categories.SHOP_WHOLESALE, item)

            if store["hasBusinessDepartment"] is True:
                item["name"] = "Costco Business Center"
            else:
                item["name"] = "Costco"

            yield item
