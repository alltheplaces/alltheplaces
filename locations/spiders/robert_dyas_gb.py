import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class RobertDyasGBSpider(Spider):
    name = "robert_dyas_gb"
    item_attributes = {"brand": "Robert Dyas", "brand_wikidata": "Q7343720"}
    start_urls = ["https://www.robertdyas.co.uk/storefinder"]
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Host": "www.robertdyas.co.uk"}}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        scripttext = response.xpath('//script[contains(text(), "Astound_StoreLocator")]').get()
        data = re.search(r'(?<="data" : ).*(?=,\s+"template")', scripttext).group(0)
        jsondata = json.loads(data)
        for location in jsondata["locations"]:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["email"] = location["cs_email"]
            item["opening_hours"] = location["hours"].replace(", ", ";")
            item["branch"] = item.pop("name")
            apply_category(Categories.SHOP_HARDWARE, item)
            yield item
