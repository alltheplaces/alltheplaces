from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class NordeaSpider(Spider):
    name = "nordea"
    item_attributes = {"brand": "Nordea", "brand_wikidata": "Q1123823"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for country in ["se", "no", "dk", "fi"]:
            yield JsonRequest(
                url="https://public-api.nordea.com/api/dbf/ca/nordea-locations-v1/branches-and-atms",
                data={
                    "country": country,
                    "coordinate1": "",
                    "coordinate2": "",
                    "category": "ALL",
                    "services": [],
                    "currencies": [],
                },
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["collection_of_atms_and_branches"]:
            item = DictParser.parse(location)
            item["lat"] = location["coordinate1"]
            item["lon"] = location["coordinate2"]
            item["city"] = item.pop("state", None)

            location_type = location.get("typeof", "")
            if location_type == "branch":
                apply_category(Categories.BANK, item)
            elif location_type == "atm":
                apply_category(Categories.ATM, item)
            elif location_type == "depmachine":
                apply_category(Categories.ATM, item)
                apply_yes_no(Extras.CASH_IN, item, True)
            else:
                self.logger.error("Unexpected category: {}".format(location_type))

            yield item
