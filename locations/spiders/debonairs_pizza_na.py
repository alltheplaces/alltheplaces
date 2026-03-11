from typing import Any

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.debonairs_pizza import DEBONAIRS_SHARED_ATTRIBUTES


class DebonairsPizzaNASpider(Spider):
    name = "debonairs_pizza_na"
    item_attributes = DEBONAIRS_SHARED_ATTRIBUTES
    start_urls = ["https://app.debonairspizza.co.na/management/api/store/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for result in response.json():
            for area in result.get("Areas", []):
                for store_info in area.get("Stores", []):
                    yield JsonRequest(
                        url=f'https://app.debonairspizza.co.na/management/api/storeinfo?storeId={store_info["Id"]}',
                        callback=self.parse_store,
                    )

    def parse_store(self, response: Response, **kwargs: Any) -> Any:
        store = response.json()
        item = DictParser.parse(store)
        item["website"] = (
            f'https://app.debonairspizza.co.na/restaurant/{item["ref"]}/{item["name"].lower().replace(" ", "-")}'
        )
        item["branch"] = item.pop("name").removeprefix("Debonairs Pizza ")
        item["opening_hours"] = self.parse_opening_hours(store.get("TradingHours", []))
        yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        opening_hours = OpeningHours()
        for rule in rules:
            opening_hours.add_range(rule["DayAsString"], rule["OpenTime"], rule["CloseTime"], "%H:%M:%S")
        return opening_hours
