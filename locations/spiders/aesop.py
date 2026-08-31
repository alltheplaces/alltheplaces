from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class AesopSpider(Spider):
    name = "aesop"
    item_attributes = {"brand": "Aesop", "brand_wikidata": "Q4688560"}
    start_urls = ["https://www.aesop.com.hk/skin/store-list.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for key, value in response.json().items():
            for location in value:
                if "aesop" in location.get("store_name").lower():
                    item = DictParser.parse(location)
                    item["branch"] = item["ref"] = item.pop("name").replace("Aesop ", "")
                    item["country"] = key
                    if "http" not in item.get("website"):
                        item.pop("website")
                    try:
                        oh = OpeningHours()
                        oh.add_ranges_from_string(location.get("store_time"))
                        item["opening_hours"] = oh
                    except:
                        pass
                    yield item
