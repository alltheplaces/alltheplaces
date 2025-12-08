import json
import re

import scrapy

from locations.dict_parser import DictParser


class BigmatBESpider(scrapy.Spider):
    name = "bigmat_be"
    item_attributes = {"brand": "BigMat", "brand_wikidata": "Q101851862"}
    start_urls = ["https://www.bigmat.be/magasins"]

    def parse(self, response, **kwargs):
        pattern = r"var\s+elements\s*=\s*(\[.*?\]);\s*var"
        stores_json = json.loads(re.search(pattern, response.text, re.DOTALL).group(1))
        for store in stores_json:
            item = DictParser.parse(store)
            item["website"] = store.get("link")
            yield item
