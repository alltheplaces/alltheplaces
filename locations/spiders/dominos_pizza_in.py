import json
from typing import Iterator

import scrapy
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.items import Feature


class DominosPizzaINSpider(Spider):
    name = "dominos_pizza_in"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    start_urls = ["https://www.dominos.co.in/store-location"]

    def parse(self, response: Response) -> Iterator[Feature]:
        for city in json.loads(response.xpath("//brand-city-list//@data-results").get()):
            yield scrapy.Request(url=f"https://www.dominos.co.in/store-location/{city}", callback=self.parse_city)

    def parse_city(self, response: Response) -> Iterator[Feature]:
        for stores_data in json.loads(response.xpath("//brand-store-list//@data-results").get()):
            for store in stores_data.get("storeStationDetails"):
                item = DictParser.parse(store.get("store"))
                item["branch"] = item.pop("name")
                item["website"] = response.url
                yield item
