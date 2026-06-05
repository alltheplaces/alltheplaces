import json
from typing import Any

import json5
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class BpsPLSpider(Spider):
    name = "bps_pl"
    item_attributes = {"brand": "Bank Polskiej Spółdzielczości", "brand_wikidata": "Q9165001"}
    start_urls = ["https://mojbank.pl/znajdz-placowke"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        token = json.loads(response.xpath('//script[@type="application/json"]/text()').get()).get("csrf.token")
        yield JsonRequest(
            url="https://mojbank.pl/znajdz-placowke?view=maps&amp;format=json&amp;task=getpoints&menuitem=145&{}=1".format(
                token
            ),
            callback=self.parse_banks,
        )
        yield JsonRequest(
            url="https://mojbank.pl/bankomaty?view=maps&amp;format=json&amp;task=getpoints&menuitem=210&{}=1".format(
                token
            ),
            callback=self.parse_atms,
        )

    def parse_banks(self, response: Response, **kwargs: Any) -> Any:
        for location in json5.loads(response.text).get("data", {})["department"]:
            if location.get("bank") == "BPS":
                item = DictParser.parse(location)
                item["street_address"] = item.pop("street")
                apply_category(Categories.BANK, item)
                yield item

    def parse_atms(self, response: Response, **kwargs: Any) -> Any:
        for location in json5.loads(response.text).get("data", {})["atm"]:
            if location.get("name", "").startswith("Bank Spółdzielczy"):
                item = DictParser.parse(location)
                item["street_address"] = item.pop("street")
                apply_category(Categories.ATM, item)
                yield item
