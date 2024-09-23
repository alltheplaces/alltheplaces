import html
from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser


class JDWetherspoonSpider(Spider):
    name = "j_d_wetherspoon"
    item_attributes = {"brand": "Wetherspoon", "brand_wikidata": "Q6109362"}
    start_urls = ["https://www.jdwetherspoon.com/pub-search/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(
            response.xpath('//script[@id="filter-google-maps-js-after"]/text()').get()
        ):
            item = DictParser.parse(location)
            item["name"] = html.unescape(item["name"])
            item["image"] = location["featured_image"]
            item["ref"] = item["website"]

            yield item
