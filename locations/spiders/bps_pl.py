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
        token_data = response.xpath('//*[@type="application/json"]/text()').get()
        token = json.loads(token_data).get("csrf.token")
        yield JsonRequest(
            url=f"https://www.bankbps.pl/znajdz-placowke?view=maps&format=json&task=getpoints&menuitem=145&{token}=1",
            callback=self.parse_details,
        )

    def parse_details(self, response: Response, **kwargs: Any) -> Any:
        data = response.json().get("data", {})
        for location_type, category in [("department", Categories.BANK), ("atm", Categories.ATM)]:
            for location in data.get(location_type, []):
                if location_type == "atm" and not location["name"].startswith("Bank Spółdzielczy"):
                    continue
                yield self.parse_location(location, category)

    def parse_location(self, location: dict, category: Categories) -> dict:
        item = DictParser.parse(location)
        item["branch"] = item.pop("name", None)
        item["name"] = self.item_attributes["brand"]
        apply_category(category, item)
        return item
