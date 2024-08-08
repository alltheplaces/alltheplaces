import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class PizzaHutMYSpider(scrapy.Spider):
    name = "pizza_hut_my"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    requires_proxy = True

    def start_requests(self):
        headers = {"Client": "236e3ed4-3038-441a-be5b-417871eb84d4"}
        yield scrapy.Request(
            url="https://apiapse1.phdvasia.com/v1/product-hut-fe/localizations?limit=10000",
            headers=headers,
            callback=self.parse,
        )

    def parse(self, response, **kwargs):
        for store in response.json()["data"]["items"]:
            item = DictParser.parse(store)
            item["website"] = "https://www.pizzahut.com.my/"
            apply_category(Categories.RESTAURANT, item)
            yield item
