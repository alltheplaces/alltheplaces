import json
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class FletcherHotelNLSpider(scrapy.Spider):
    name = "fletcher_hotel_nl"
    item_attributes = {"brand": "Fletcher Hotel", "brand_wikidata": "Q67203020"}
    start_urls = ["https://www.fletcher.nl"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        path = response.xpath("//@data-marker").get()
        yield scrapy.Request(url="https://www.fletcher.nl" + path, callback=self.parse_details)

    def parse_details(self, response, **kwargs):
        raw_data = json.loads((response.text).replace("window.mapMarkers = ", "").replace(";", "")).values()
        for hotel in raw_data:
            item = DictParser.parse(hotel)
            item["branch"] = item.pop("name")
            item["city"], item["state"] = hotel["place"].split(",")
            apply_category(Categories.HOTEL, item)
            yield item
