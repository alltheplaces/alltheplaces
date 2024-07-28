import scrapy

from locations.categories import Categories
from locations.dict_parser import DictParser


class NissanCZSpider(scrapy.Spider):
    name = "nissan_cz"
    item_attributes = {"brand": "Nissan", "brand_wikidata": "Q20165", "extras": Categories.SHOP_CAR.value}
    start_urls = [
        "https://ni-content.hu/nissan-dealers/Data/data_cz.json",
    ]

    def parse(self, response, **kwargs):
        for store in response.json()["dealers"]:
            item = DictParser.parse(store)
            item["ref"] = store.get("code")
            item["lat"] = store.get("lattitude")
            yield item
