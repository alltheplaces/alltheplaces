from typing import AsyncIterator

from scrapy.http import JsonRequest

from locations.geo import city_locations
from locations.spiders.dominos_pizza_au import DominosPizzaAUSpider


class DominosPizzaJPSpider(DominosPizzaAUSpider):
    name = "dominos_pizza_jp"
    item_attributes = {"brand_wikidata": "Q839466"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for city in city_locations("JP", 10000):
            yield JsonRequest(
                url=f"https://www.dominos.jp/dynamicstoresearchapi/getstoresfromquery?lon={city['longitude']}&lat={city['latitude']}"
            )
