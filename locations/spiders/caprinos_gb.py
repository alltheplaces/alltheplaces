from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class CaprinosGBSpider(Spider):
    name = "caprinos_gb"
    item_attributes = {"brand": "Caprinos", "brand_wikidata": "Q125623745"}
    start_urls = ["https://www.caprinospizza.co.uk/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "var shops =")]/text()').get()
        ):
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["phone"] = location["restaurant_info"].split("<br/>")[1]

            yield item
