import json

import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class PizzaHutTHSpider(scrapy.Spider):
    name = "pizza_hut_th"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"user-agent": BROWSER_DEFAULT}}
    start_urls = ["https://www.pizzahut.co.th/"]

    def parse(self, response, **kwargs):
        token = response.xpath('//meta[@name="csrf-token"]/@content').get()
        yield JsonRequest(
            url="https://www.pizzahut.co.th/location-get-stores-by-search",
            method="POST",
            headers={"X-CSRF-TOKEN": token},
            callback=self.parse_stores,
        )

    def parse_stores(self, response):
        for store in json.loads(response.json()["data"]):
            item = DictParser.parse(store)
            item["addr_full"] = store.get("store_address")
            item["state"] = store.get("store_province")
            apply_category(Categories.RESTAURANT, item)

            yield item
