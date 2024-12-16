from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingGTSpider(Spider):
    name = "burger_king_gt"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES

    def start_requests(self) -> Iterable[Request]:
        # https://api.bk.gt/v1/restaurant/nearby?latitude=14.587041&longitude=-90.5210362 this API currently leads to
        # HTTP Error 500, but might fetch more POIs if works.
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
            item["branch"] = item.pop("name").removeprefix("BK ").removeprefix("Burger King ")
            item["website"] = "https://app.bk.gt/#/"
            apply_yes_no(Extras.KIDS_AREA, item, location.get("kidsZone"))
            apply_yes_no(Extras.BREAKFAST, item, location.get("breakfast"))
            apply_yes_no(Extras.DELIVERY, item, location.get("delivery"))
            apply_yes_no(Extras.WIFI, item, location.get("wifi"))
            apply_yes_no(Extras.SELF_CHECKOUT, item, location.get("selfService"))
            yield item
