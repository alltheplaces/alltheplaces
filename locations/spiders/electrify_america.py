import json
import random

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class ElectrifyAmericaSpider(scrapy.Spider):
    name = "electrify_america"
    item_attributes = {"brand": "Electrify America", "brand_wikidata": "Q59773555"}
    start_urls = ["https://api-prod.electrifyamerica.com/v2/locations"]

    def parse(self, response):
        for item in response.json():
            feature = DictParser.parse(item)

            feature["extras"]["capacity"] = item.get("evseMax")

            if access := item.get("type"):
                if access == "PUBLIC":
                    feature["extras"]["access"] = "public"

            yield feature
