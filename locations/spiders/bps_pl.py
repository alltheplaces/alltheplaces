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
        token_data = response.xpath('//*[@type="application/json"]/text()').get()
        token = json.loads(token_data).get("csrf.token")
        for location_type, value in [("znajdz-placowke", "145"), ("bankomaty", "210")]:
            yield JsonRequest(
                url=f"https://mojbank.pl/{location_type}?view=maps&amp;format=json&amp;task=getpoints&menuitem={value}&{token}=1",
                callback=self.parse_details,
            )

    def parse_details(self, response: Response, **kwargs: Any) -> Any:
        data = json5.loads(response.text).get("data", {})

        # Process branches
        for location in data.get("department", []):
            if location.get("bank") == "BPS":
                item = DictParser.parse(location)
                apply_category(Categories.BANK, item)
                yield item

        # Process ATMs
        for location in data.get("atm", []):
            if location.get("name", "").startswith("Bank Spółdzielczy"):
                item = DictParser.parse(location)
                apply_category(Categories.ATM, item)
                yield item
