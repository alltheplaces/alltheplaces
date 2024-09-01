from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class ChargyLUSpider(Spider):
    name = "chargy_lu"
    item_attributes = {"brand": "Chargy", "brand_wikidata": "Q62702950"}
    start_urls = ["https://chargy.lu/en/"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "terminalsJson")]/text()').get()
        ):
            item = DictParser.parse(location)

            apply_category(Categories.CHARGING_STATION, item)
            yield item
