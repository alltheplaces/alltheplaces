import scrapy

from locations.categories import Categories
from locations.dict_parser import DictParser


class DecathlonSGSpider(scrapy.Spider):
    name = "decathlon_sg"
    item_attributes = {"brand": "Decathlon", "brand_wikidata": "Q509349", "extras": Categories.SHOP_SPORTS.value}
    start_urls = [
        "https://www.decathlon.sg/api/store-setting?countryCode=SG",
    ]

    def parse(self, response, **kwargs):
        for store in response.json():
            store.update(store.pop("address"))
            item = DictParser.parse(store)
            yield item
