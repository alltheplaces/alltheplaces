import json
from typing import Any

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class BpsPLSpider(scrapy.Spider):
    name = "bps_pl"
    item_attributes = {"brand": "Bank Polskiej Spółdzielczości", "brand_wikidata": "Q9165001"}
    start_urls = ["https://www.bankbps.pl/znajdz-placowke"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        token = json.loads(response.xpath('//*[@type="application/json"]/text()').get())["csrf.token"]
        yield JsonRequest(
            url=f"https://www.bankbps.pl/znajdz-placowke?view=maps&amp;format=json&amp;task=getpoints&menuitem=145&{token}=1",
            callback=self.parse_details,
        )

    def parse_details(self, response, **kwargs):
        for location in response.json()["data"]["department"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["name"] = self.item_attributes["brand"]
            apply_category(Categories.BANK, item)
            yield item
