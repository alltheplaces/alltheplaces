from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class VanDerValkSpider(Spider):
    name = "van_der_valk"
    item_attributes = {"brand": "Van der Valk", "brand_wikidata": "Q2802214"}
    start_urls = ["https://www.valk.com/ajax.cfm?event=ajax.get&type=content&name=proxy&action=apiToken"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield JsonRequest(
            url="https://api.vandervalkonline.com/api/v2/hotels?token={}".format(response.json()["data"]["token"]),
            callback=self.parse_request,
        )

    def parse_request(self, response: Response) -> Any:
        for hotel in response.json().get("data"):
            name = hotel.pop("name")
            item = DictParser.parse(hotel)
            item["branch"] = name.get("full")
            if item["website"] and "http" not in item["website"]:
                item["website"] = "https://" + item["website"]
            apply_category(Categories.HOTEL, item)
            yield item
