import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class DerendingerCHSpider(Spider):
    name = "derendinger_ch"
    item_attributes = {"brand": "Derendinger", "brand_wikidata": "Q1200150"}
    start_urls = ["https://www.derendinger.ch/de/filialen"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.xpath('//input[@id="map-data"]/@value').get()):
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["branch"] = item.pop("name")
            apply_category(Categories.SHOP_CAR_PARTS, item)
            yield item
