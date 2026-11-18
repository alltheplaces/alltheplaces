from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class PepcoSpider(Spider):
    name = "pepco"
    item_attributes = {"brand": "Pepco", "brand_wikidata": "Q11815580"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Any]:
        for country in [
            "AT",
            "BA",
            "BG",
            "CZ",
            "DE",
            "EE",
            "ES",
            "GR",
            "HR",
            "HU",
            "IT",
            "LT",
            "LV",
            "MK",
            "PL",
            "PT",
            "RO",
            "RS",
            "SI",
            "SK",
        ]:
            yield JsonRequest(url=f"https://pepco.pl/api/stores?market={country}", callback=self.parse)

    def parse(self, response: Response) -> Iterable[Any]:
        for location in response.json().get("globalStoreDataSet").get("stores").get("features"):
            location.update(location.pop("properties"))
            item = DictParser.parse(location)
            item["name"] = None
            try:
                oh = OpeningHours()
                for hours_text in location.get("opening_hours"):
                    for day in hours_text.get("days"):
                        open_time = hours_text.get("from")
                        close_time = hours_text.get("to")
                        oh.add_range(day, open_time, close_time)
                item["opening_hours"] = oh
            except:
                pass
            apply_category(Categories.SHOP_CLOTHES, item)

            yield item
