from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class NordeaSESpider(Spider):
    name = "nordea_se"
    item_attributes = {"brand": "Nordea", "brand_wikidata": "Q1123823"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://public-api.nordea.com/api/dbf/ca/nordea-locations-v1/branches-and-atms",
            data={
                "country": "se",
                "coordinate1": "",
                "coordinate2": "",
                "category": "ALL",
                "services": [],
                "currencies": [],
            },
            method="POST",
            callback=self.parse,
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for bank in response.json()["collection_of_atms_and_branches"]:
            item = DictParser.parse(bank)
            item["lat"] = bank["coordinate1"]
            item["lon"] = bank["coordinate2"]
            apply_category(Categories.BANK, item)
            yield item
