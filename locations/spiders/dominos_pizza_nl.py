from typing import Iterable

from scrapy.http import JsonRequest

from locations.geo import city_locations
from locations.spiders.dominos_pizza_au import DominosPizzaAUSpider


class DominosPizzaNLSpider(DominosPizzaAUSpider):
    name = "dominos_pizza_nl"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}

    def start_requests(self) -> Iterable[JsonRequest]:
        for city in city_locations("NL", 15000):
            yield JsonRequest(
                url=f"https://www.dominos.nl/dynamicstoresearchapi/getstoresfromquery?lon={city['longitude']}&lat={city['latitude']}",
            )
