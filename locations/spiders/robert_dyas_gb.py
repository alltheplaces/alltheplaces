import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class RobertDyasGBSpider(Spider):
    name = "robert_dyas_gb"
    item_attributes = {"brand": "Robert Dyas", "brand_wikidata": "Q7343720"}
    start_urls = ["https://www.robertdyas.co.uk/storefinder"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "Host": "www.robertdyas.co.uk",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "DNT": "1",
        },
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        scripttext = response.xpath('//script[contains(text(), "Astound_StoreLocator")]').get()
        data = re.search(r'(?<="data" : ).*(?=,\s+"template")', scripttext).group(0)
        jsondata = json.loads(data)
        for location in jsondata["locations"]:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["email"] = location["cs_email"]
            item["opening_hours"] = location["hours"].replace(", ", ";")
            item["branch"] = item["name"]
            yield item
