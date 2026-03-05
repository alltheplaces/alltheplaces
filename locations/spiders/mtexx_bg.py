from typing import Any

import chompjs
import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.react_server_components import parse_rsc


class MtexxBGSpider(scrapy.Spider):
    name = "mtexx_bg"
    item_attributes = {"operator": "M-Texx", "operator_wikidata": "Q122947768"}
    start_urls = ["https://m-texx.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        scripts = response.xpath('//*[contains(text(),"coordinates")]/text()').getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join([s for n, s in objs]).encode()
        raw_data = DictParser.get_nested_key(dict(parse_rsc(rsc)), "initialCities")
        for location in raw_data:
            for local in location["locations"]:
                item = DictParser.parse(local)
                item["name"] = item["name"].split(" - ")[0]
                item["lat"], item["lon"] = local["coordinates"]
                yield item
