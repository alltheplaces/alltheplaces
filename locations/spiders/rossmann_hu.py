import json
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_HU, OpeningHours, sanitise_day


class RossmannHUSpider(Spider):
    name = "rossmann_hu"
    item_attributes = {"brand": "Rossmann", "brand_wikidata": "Q316004"}

    async def start(self) -> AsyncIterator[Request]:
        query = """
        {
            stores {
                id
                zip_code
                city
                lat
                lng
                street
                openings
            }
        }
        """
        payload = {"query": query}
        headers = {"Content-Type": "application/json"}
        yield Request(
            url="https://api.rossmann.hu/graphql",
            method="POST",
            body=json.dumps(payload),
            headers=headers,
            callback=self.parse,
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]["stores"]:
            item = DictParser.parse(store)
            item["street_address"] = item.pop("street").removesuffix(".")
            item["postcode"] = str(item["postcode"])
            item["opening_hours"] = self.parse_opening_hours(store["openings"])
            yield item

    def parse_opening_hours(self, openings: str) -> OpeningHours:
        oh = OpeningHours()
        try:
            for rule in openings.split("\n"):
                day, times = rule.split(": ", maxsplit=1)
                if times == "Zárva":
                    oh.set_closed(sanitise_day(day, DAYS_HU))
                else:
                    oh.add_range(sanitise_day(day, DAYS_HU), *times.split("-"))
        except Exception as e:
            self.logger.warning(f"Failed to parse opening hours: {e}")
        return oh
