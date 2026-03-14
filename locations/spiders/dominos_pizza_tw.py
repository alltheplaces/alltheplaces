from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.user_agents import BROWSER_DEFAULT


class DominosPizzaTWSpider(Spider):
    name = "dominos_pizza_tw"
    item_attributes = {"brand_wikidata": "Q839466"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for city in city_locations("TW", 16000):
            yield JsonRequest(
                url=f"https://www.dominos.com.tw/dynamicstoresearchapi/getstoresfromquery?lon={city['longitude']}&lat={city['latitude']}&count=100000"
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for restaurant in response.json()["PickupSearchStore"]:
            restaurant.update(restaurant["locations"][0].pop("address"))
            item = DictParser.parse(restaurant)
            item["branch"] = item.pop("name")
            item["ref"] = restaurant["storeNo"]
            for address in restaurant["attributes"]:
                if address["key"] == "streetName":
                    item["street_address"] = address["value"]
                elif address["key"] == "state":
                    item["state"] = address["value"]
                elif address["key"] == "suburb":
                    item["city"] = address["value"]
                elif address["key"] == "postCode":
                    item["postcode"] = address["value"]
            yield item
