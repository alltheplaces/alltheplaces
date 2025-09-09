from typing import Any

import scrapy
import xmltodict
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


# TODO: Is this fully covered by the BMW Group Spider? It uses a very similar API endpoint
class MiniBESpider(scrapy.Spider):
    name = "mini_be"
    item_attributes = {"brand": "Mini", "brand_wikidata": "Q116232"}
    allowed_domains = ["mini.be"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}
    start_urls = [
        "https://c2b-services.bmw.com/c2b-localsearch/services/api/v4/clients/BMWSTAGE2_DLO/-/pois?category=MI&maxResults=2000&showAll=true&country=BE"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if "xml" in str(response.headers.get("content-type")):
            data = xmltodict.parse(response.body)
            pois = data.get("result", {}).get("data", {}).get("pois", {}).get("poi")
        else:
            pois = response.json().get("status", {}).get("data", {}).get("pois")

        for row in pois:
            item = DictParser.parse(row)
            item["ref"] = row.get("key")
            item["phone"] = row.get("attributes", {}).get("phone")
            item["email"] = row.get("attributes", {}).get("mail")
            item["website"] = row.get("attributes", {}).get("homepage")

            apply_category(Categories.SHOP_CAR, item)

            yield item
