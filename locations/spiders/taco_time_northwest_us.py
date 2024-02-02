import json

import scrapy

from locations.dict_parser import DictParser


class TacoTimeNorthwestUSSpider(scrapy.Spider):
    name = "taco_time_northwest_us"
    item_attributes = {"brand_wikidata": "Q7673970"}
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
            item["extras"]["website:menu"] = store["order"]
            item["website"] = "https://tacotimenw.com/find-us/{}/".format(store["order"].split("/")[-1])
            item["name"] = item["name"].replace("&#8211;", "–")
            yield item
