from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class NravizzaBYSpider(Spider):
    name = "nravizza_by"
    item_attributes = {"brand_wikidata": "Q125747982"}
    start_urls = ["https://nravizza.by/page9609244.html"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "arMapMarkers")]/text()').get()
        ):
            item = DictParser.parse(location)
            item["street_address"] = item.pop("name")
            yield item
