import json
from typing import Any

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser


class TuevNordDESpider(scrapy.Spider):
    name = "tuev_nord_de"
    item_attributes = {"brand": "TÜV Nord", "brand_wikidata": "Q2463547"}
    start_urls = ["https://www.tuev-nord.de/de/privatkunden/tuev-stationen/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data_locations = json.loads(response.xpath("//div/@data-locations").get())
        for location in data_locations:
            item = DictParser.parse(location)
            item["website"] = response.urljoin(location.pop("link"))
            yield item
