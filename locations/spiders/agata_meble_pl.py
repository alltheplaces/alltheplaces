from urllib.parse import urljoin

import scrapy

from locations.dict_parser import DictParser


class AgataMeblePLSpider(scrapy.Spider):
    name = "agata_meble_pl"
    item_attributes = {"brand": "Agata Meble", "brand_wikidata": "Q9141928"}
    start_urls = ["https://www.agatameble.pl/api/v1/pos/pos/poses.json"]

    def parse(self, response):
        for poi in response.json()["results"]:
            # Skip disabled results
            if poi["Enabled"] is False:
                continue

            item = DictParser.parse(poi)
            item.pop("name", None)
            item["website"] = urljoin("https://www.agatameble.pl/salon/", poi["Slug"])

            # Make a request to the website so that we filter out closed stores that 404
            yield scrapy.Request(item["website"], self.parse_store, meta={"item": item})

    def parse_store(self, response, **kwargs):
        item = response.meta["item"]
        yield item
