import json

import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class TerstalNLSpider(scrapy.Spider):
    name = "terstal_nl"
    item_attributes = {"brand": "terStal", "brand_wikidata": "Q114905394"}

    def start_requests(self):
        yield JsonRequest(url="https://www.terstal.nl/rest/V1/stores/store_id/1")

    def parse(self, response, **kwargs):
        for store in json.loads(response.text):
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
