from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class PizzaHutQASpider(Spider):
    name = "pizza_hut_qa"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}

    def start_requests(self):
        yield JsonRequest(
            url="https://www.qatar.pizzahut.me/api/stores",
            headers={"franchiseid": "3"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["Data"]:
            item = DictParser.parse(store)
            item["street_address"] = clean_address([store.get("address1"), store.get("address2")])
            item["website"] = "https://www.qatar.pizzahut.me/"
            apply_category(Categories.RESTAURANT, item)
            yield item
