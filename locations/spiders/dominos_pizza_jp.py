from typing import Iterable

from scrapy.http import JsonRequest

from locations.geo import city_locations
from locations.spiders.dominos_pizza_au import DominosPizzaAUSpider
from locations.user_agents import BROWSER_DEFAULT


class DominosPizzaJPSpider(DominosPizzaAUSpider):
    name = "dominos_pizza_jp"
    item_attributes = {
        "brand_wikidata": "Q839466",
        "country": "JP",
    }
    user_agent = BROWSER_DEFAULT

    def start_requests(self) -> Iterable[JsonRequest]:
        for city in city_locations("JP", 10000):
            yield JsonRequest(
                url=f"https://www.dominos.jp/dynamicstoresearchapi/getstoresfromquery?lon={city['longitude']}&lat={city['latitude']}"
            )
