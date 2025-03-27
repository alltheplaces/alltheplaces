import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_HU, OpeningHours, sanitise_day


class RossmannHUSpider(Spider):
    name = "rossmann_hu"
    item_attributes = {"brand": "Rossmann", "brand_wikidata": "Q316004"}
    start_urls = ["https://shop.rossmann.hu/uzletkereso"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.xpath('//script[@id="__NEXT_DATA__"][@type="application/json"]/text()').get()
        data = json.loads(data)
        for store in data["props"]["pageProps"]["baseStores"]:
            item = DictParser.parse(store)
            item.pop("name")
            item["postcode"] = str(item.get("postcode") or "")
            item["street_address"] = item.pop("street")

            item["opening_hours"] = self.parse_opening_hours(store["openings"])

            yield item

    def parse_opening_hours(self, openings: str) -> OpeningHours:
        oh = OpeningHours()

        for rule in openings.split("\n"):
            day, times = rule.split(": ", maxsplit=1)
            if times == "Zárva":
                oh.set_closed(sanitise_day(day, DAYS_HU))
            else:
                oh.add_range(sanitise_day(day, DAYS_HU), *times.split("-"))

        return oh
