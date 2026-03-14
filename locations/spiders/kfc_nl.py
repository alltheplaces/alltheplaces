from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES


class KfcNLSpider(Spider):
    name = "kfc_nl"
    item_attributes = KFC_SHARED_ATTRIBUTES

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://245fidy0v1-3.algolianet.com/1/indexes/production_0_locations_all/query?x-algolia-api-key=e24223afcd0148f3679075ed6c8d3767&x-algolia-application-id=245FIDY0V1",
            data={"aroundLatLngViaIP": True, "aroundRadius": "all", "hitsPerPage": 10000},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["hits"]:
            item = DictParser.parse(location)
            item["ref"] = location["objectID"]
            item["lat"] = location["_geoloc"]["lat"]
            item["lon"] = location["_geoloc"]["lng"]
            item["phone"] = location["address"]["phoneNumber"]
            item["opening_hours"] = self.parse_hours(location["openingHours"])

            apply_category(Categories.FAST_FOOD, item)

            yield item

    def parse_hours(self, rules: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            oh.add_range(DAYS[rule["dayOfWeek"] - 1], rule["startTime"], rule["endTime"])
        return oh
