import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.mcdonalds import McDonaldsSpider


class McDonaldsITSpider(scrapy.Spider):
    name = "mcdonalds_it"
    item_attributes = McDonaldsSpider.item_attributes
    start_urls = ["https://www.mcdonalds.it/static/json/store_locator.json"]

    def parse(self, response):
        for store in response.json()["sites"]:
            store["street_address"] = store.pop("address")
            item = DictParser.parse(store)
            item["website"] = "https://www.mcdonalds.it/ristorante/" + store["uri"]
            apply_category(Categories.FAST_FOOD, item)
            yield item
