import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class WingstopMXSpider(Spider):
    name = "wingstop_mx"
    item_attributes = {"brand": "Wingstop", "brand_wikidata": "Q8025339"}
    start_urls = ["https://wingstopmexico.com/wp-admin/admin-ajax.php?action=asl_load_stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.text):
            item = DictParser.parse(location)
            item["street_address"] = item.pop("street")
            yield item
