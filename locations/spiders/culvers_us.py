from typing import Any, Iterable

import scrapy
from scrapy import Request
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.geo import city_locations


class CulversUSSpider(scrapy.Spider):
    name = "culvers_us"
    item_attributes = {"brand": "Culver's", "brand_wikidata": "Q1143589"}

    async def start(self) -> Iterable[Request]:
        for city in city_locations("US", 100000):
            yield JsonRequest(
                url=f'https://www.culvers.com/api/locator/getLocations?lat={city["latitude"]}&long={city["longitude"]}&radius=600000&limit=10000'
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["geofences"]:
            location.update(location.pop("metadata"))
            location.pop("geometry")
            item = DictParser.parse(location)
            item["ref"] = location["_id"]
            item["name"] = self.item_attributes["brand"]
            item["lon"], item["lat"] = location["geometryCenter"]["coordinates"]
            item["website"] = "https://www.culvers.com/restaurants/" + location["slug"]
            yield item
