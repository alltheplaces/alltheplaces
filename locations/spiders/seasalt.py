import json
import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser

class SeasaltSpider(scrapy.Spider):
    name = "seasalt"
    item_attributes = {
        "brand": "Seasalt",
        "brand_wikidata": "Q107344382",
    }

    start_urls = ["https://www.seasaltcornwall.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        mapdata = response.xpath('//script[contains(text(), "lng")]/text()').get()
        data1 = json.loads(mapdata)
        for value in data1:
            data=data1[value]["amLocator"]["jsonStoreLocations"]["items"]

        for location in data:
            temp=location["popup_html"]
            result=re.search(
                r"locator.title[^>]+>([^<]+)</div>(?:</a>)*</h3>\s+([^<]+)\s+<br><span",
                temp,
            )
            location["name"]=result.group(1)
            location["address"]=result.group(2)
            item = DictParser.parse(location)

            yield item
