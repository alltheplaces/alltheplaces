import re
from typing import Any

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories
from locations.dict_parser import DictParser


class JohnDorysZASpider(scrapy.Spider):
    name = "john_dorys_za"
    item_attributes = {"brand": "John Dory's", "brand_wikidata": "Q130140080", "extras": Categories.RESTAURANT.value}
    start_urls = ["https://www.johndorys.com/za/restaurants/all"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        url_key = re.findall(r"\"modifiedOn\":\d+},(\d+),", response.xpath('//*[@id="__NUXT_DATA__"]/text()').get())
        for key in url_key:
            yield JsonRequest(
                url="https://www.johndorys.com/api/gostore", data={"key": f"{key}"}, callback=self.parse_details
            )

    def parse_details(self, response):
        if data := response.json().get("res").get("store"):
            item = DictParser.parse(data)
            item["website"] = "/".join(
                [
                    "https://www.johndorys.com/za/restaurants",
                    item["state"].lower().replace(" ", "-").replace("'", ""),
                    item["name"].lower().replace(" ", "-").replace("'", ""),
                ]
            )
            yield item
