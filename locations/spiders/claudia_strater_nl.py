from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class ClaudiaStraterNLSpider(Spider):
    name = "claudia_strater_nl"
    item_attributes = {
        "brand_wikidata": "Q52903369",
        "brand": "Claudia Sträter",
    }
    start_urls = ["https://www.claudiastrater.com/over-ons/winkels/"]
    no_refs = True

    def extract_json(self, response):
        return chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "map.markers = ")]/text()').get().split("map.markers = ")[1]
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        locations = self.extract_json(response)
        for location in locations:
            item = DictParser.parse(location)
            yield from self.post_process_item(item, response, location) or []

    def post_process_item(self, item, response, location):
        print(location)
        item["name"] = item["name"].strip()
        item["website"] = location["url"].replace("~/", "https://www.claudiastrater.com/")
        item["image"] = location["imageurl"].replace("~/", "https://www.claudiastrater.com/")

        yield item
