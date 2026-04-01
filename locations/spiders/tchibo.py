import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

"""
Covers Following Countries : AT,DE,CZ,SK,HU,PL,CH,TR
"""


class TchiboSpider(Spider):
    name = "tchibo"
    item_attributes = {"brand": "Tchibo", "brand_wikidata": "Q564213"}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(
            url="https://www.tchibo.de/service/storefinder/api/plugins/storefinder/storefinder/api/stores?viewLat=0&viewLng=0&precision=1000000&size=100&page=0&storeTypeFilters=Filiale"
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json().get("content"):
            [store.update(store.pop(key)) for key in ["locationGeographicDto", "addressDto"]]
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("street")

            try:
                item["opening_hours"] = self.parse_hours(store["daysDto"])
            except:
                pass

            apply_category(Categories.COFFEE_SHOP, item)

            yield item

        current_page = response.json()["number"]
        pages = response.json()["totalPages"]
        if current_page < pages:
            url = re.sub(r"page=\d+", f"page={current_page + 1}", response.url)
            yield JsonRequest(url=url)

    def parse_hours(self, rules: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, rule in rules.items():
            if rule["morningOpening"] == rule["afternoonClosing"] == "null":
                oh.set_closed(day)
            elif rule["morningClosing"] != "null":
                oh.add_range(day, rule["morningOpening"], rule["morningClosing"])
                oh.add_range(day, rule["afternoonOpening"], rule["afternoonClosing"])
            else:
                oh.add_range(day, rule["morningOpening"], rule["afternoonClosing"].replace("23:59:59", "23:59"))
        return oh
