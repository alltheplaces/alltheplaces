from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class PizzaHutQASpider(Spider):
    name = "pizza_hut_qa"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}

    def start_requests(self):
        yield JsonRequest(url="https://www.qatar.pizzahut.me/api/customer/stores/1")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]:
            item = DictParser.parse(store)
            item["branch"] = item.pop("name").removeprefix("Pizza Hut ").removeprefix("Pizza hut ").strip()
            item["street_address"] = item.pop("addr_full", None)
            apply_category(Categories.RESTAURANT, item)
            yield item
