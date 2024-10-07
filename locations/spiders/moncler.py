from typing import Any
from requests_cache import Response
import scrapy

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT

class MonclerSpider(scrapy.Spider):
    name = "moncler"
    item_attributes = {"brand": "Moncler", "brand_wikidata": "Q1548951"}
    allowed_domains = ["moncler.com"]
    start_urls = ["https://www.moncler.com/on/demandware.store/Sites-MonclerEU-Site/it_IT/StoresApi-FindAll"]
    requires_proxy = True
    custom_settings = {"ROBOTSTXT_OBEY": False}
    user_agent = BROWSER_DEFAULT

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["state"] = location.get("stateCode")
            yield item

