from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class MoyaPLSpider(Spider):
    name = "moya_pl"
    item_attributes = {"brand": "Moya", "brand_wikidata": "Q62297700"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url="https://moyastacja.pl/mapa", data={"controller": "Main", "action": "GetMap"})

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["Elements"]:
            if not any(t in location["types"] for t in [1, 2, 3]):
                continue

            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")

            if location.get("time", "").lower() == "24h":
                item["opening_hours"] = "24/7"
            # TODO: other hours available

            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Fuel.OCTANE_95, item, 11 in location["attributes"])
            apply_yes_no(Fuel.DIESEL, item, 12 in location["attributes"])
            apply_yes_no(Fuel.LPG, item, 14 in location["attributes"])
            apply_yes_no(Fuel.ELECTRIC, item, 15 in location["attributes"])
            apply_yes_no(Fuel.OCTANE_98, item, 40 in location["attributes"])
            apply_yes_no(Extras.COMPRESSED_AIR, item, 17 in location["attributes"])
            apply_yes_no(Extras.TOILETS, item, 33 in location["attributes"])
            apply_yes_no(Extras.WIFI, item, 34 in location["attributes"])
            apply_yes_no(Extras.CAR_WASH, item, 35 in location["attributes"])
            apply_yes_no(Extras.VACUUM_CLEANER, item, 36 in location["attributes"])

            yield item
