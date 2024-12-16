from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingGTSpider(Spider):
    name = "burger_king_gt"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES

    def start_requests(self) -> Iterable[Request]:
        for city in city_locations("GT", 1000):
            yield JsonRequest(
                url="https://api.bk.gt/v1/geolocation/verifyLatLng",
                data={"lat": city["latitude"], "lng": city["longitude"]},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if result := response.json().get("data"):
            location = result.get("restaurant")
            item = DictParser.parse(location)
            item["geometry"] = location.get("point")
            yield item
