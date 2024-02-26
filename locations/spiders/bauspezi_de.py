from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from scrapy import Spider

class BauSpeziDESpider(Spider):
    name = "bauspezi_de"
    item_attributes = {
        "brand_wikidata": "Q85324366",
        "brand": "BauSpezi",
    }
    start_urls = ["https://bauspezi.de/wp-json/wpgmza/v1/features"]

    def parse(self, response, **kwargs):
        yield from map(DictParser.parse, response.json()["markers"])
