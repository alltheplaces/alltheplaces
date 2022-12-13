import json

import scrapy

from locations.items import GeojsonPointItem
from locations.dict_parser import DictParser


class AsicsDeSpider(scrapy.Spider):

    name = "asics_de"
    item_attributes = {"brand": "asics", "brand_wikidata": "Q327247"}
    allowed_domains = ["www.asics.com"]
    start_urls = ["https://cdn.crobox.io/content/ujf067/stores.json"]

    def parse(self, response):
        data_json = json.loads(response.text)
        for store in data_json:
            item = GeojsonPointItem()
            item = DictParser.parse(store)
            item["ref"] = store["name"]
            yield item
