import json
import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser


class SportClipsCASpider(scrapy.Spider):
    name = "sport_clips_ca"
    item_attributes = {"brand": "Sport Clips", "brand_wikidata": "Q7579310"}
    start_urls = ["https://sportclips.ca/store-locator"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(
            re.search(
                r"locations\":(\[.*\])};", response.xpath('//*[contains(text(),"location_map_data")]/text()').get()
            ).group(1)
        ):
            location.update(location.pop("location"))
            item = DictParser.parse(location)
            item["ref"] = item["website"] = location["permalink"]
            yield item
