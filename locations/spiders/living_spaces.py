
from typing import Any
from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser

class LivingSpacesSpider(Spider):
    name = "living_spaces"
    item_attributes = {"brand": "Living Spaces", "brand_wikidata": "Q63626177"}
    start_urls = ["https://www.livingspaces.com/api/navigationapi/getStores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["ref"] = location["code"]
            item["branch"] = item.pop("name")
            item["website"] = "https://www.livingspaces.com" + location["storePageUrl"]
            yield item

