from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class PizzaHutLUSpider(Spider):
    name = "pizza_hut_lu"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        # https://restaurants.pizzahut.lu/ provide few locations and without coordinates.
        yield JsonRequest(
            url="https://takeout.pizzahut.lu/api/1/restaurants/",
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("Pizza Hut ")
            item["geometry"] = location.get("coordinate")
            item["addr_full"] = merge_address_lines([location.get("address"), location.get("address_2")])
            email = location.get("email") or ""
            item["email"] = email if "@test.com" not in email else None
            apply_category(Categories.RESTAURANT, item)
            yield item
