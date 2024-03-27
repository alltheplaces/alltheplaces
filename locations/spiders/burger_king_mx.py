from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingMXSpider(Spider):
    name = "burger_king_mx"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            "https://api-lac.menu.app/api/directory/search?page=1",
            headers={"Application": "4160ef94dff50c0ea5067b489653eae0"},
            data={"latitude": "0", "longitude": "0", "view": "search", "per_page": 500},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["venues"]["data"]:
            location = location["venue"]
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["state"] = None

            yield item
