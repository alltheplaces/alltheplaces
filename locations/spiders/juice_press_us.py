import re
from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class JuicePressUSSpider(Spider):
    name = "juice_press_us"
    item_attributes = {"brand": "Juice Press", "brand_wikidata": "Q27150131"}
    start_urls = ["https://www.juicepress.com/pages/location"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = list(
            chompjs.parse_js_objects(
                re.search(r"JPSTORELOCATOR\.locations\.push\((.*)\);Object", response.text, re.DOTALL).group(1)
            )
        )
        for store in raw_data:
            item = DictParser.parse(store)
            item["street_address"] = item.pop("name")
            item["image"] = store["image"]
            item["ref"] = store["selector"]

            if float(item["lon"]) > 0:
                item["lon"] = float(item["lon"]) * -1
            yield item
