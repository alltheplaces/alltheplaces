import scrapy

from locations.dict_parser import DictParser


class CaliforniaPizzaKitchenSpider(scrapy.Spider):
    name = "california_pizza_kitchen"
    item_attributes = {
        "brand": "California Pizza Kitchen",
        "brand_wikidata": "Q15109854",
        "country": "US",
    }
    start_urls = ["https://api.cpk.com/api/v1.0/restaurants/cpk-stores"]

    def parse(self, response):
        store_data = response.json()["data"]["restaurants"]

        for store in store_data:
            store["street_address"] = store.pop("address")

            item = DictParser.parse(store)

            item["website"] = f'https://www.cpk.com/locations/{item["ref"]}'

            yield item
