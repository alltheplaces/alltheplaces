from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class FarmaciasSimilaresMXSpider(Spider):
    name = "farmacias_similares_mx"
    item_attributes = {"brand_wikidata": "Q62564610"}
    start_urls = ["https://www.farmaciasdesimilares.com/getpickuppoints"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            location.update(location["address"].pop("location"))
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["housenumber"] = location["address"]["number"]
            apply_category(Categories.PHARMACY, item)
            yield item
