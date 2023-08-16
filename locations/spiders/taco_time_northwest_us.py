import json

import scrapy

from locations.dict_parser import DictParser


class TacoTimeNorthwestUSSpider(scrapy.Spider):
    name = "taco_time_northwest_us"
    item_attributes = {"brand": "Taco Time Northwest", "brand_wikidata": "Q7673970"}
    allowed_domains = ["tacotimenw.com"]
    start_urls = ["https://tacotimenw.com/find-us/"]

    def parse(self, response):
        data_raw = (
            response.xpath('//script[contains(text(), "#bh-sl-map-container")]/text()')
            .extract_first()
            .split("dataRaw: ", 1)[1]
            .split(",\n", 1)[0]
        )
        stores = json.loads(data_raw)
        for store in stores:
            item = DictParser.parse(store)
            item["image"] = store["image"]
            item["website"] = store["order"]
            item["name"] = item["name"].replace("&#8211;", "–")
            yield item
