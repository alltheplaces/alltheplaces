from typing import AsyncIterator

from scrapy.http import JsonRequest

from locations.geo import city_locations
from locations.spiders.dominos_pizza_au import DominosPizzaAUSpider


class DominosPizzaFRSpider(DominosPizzaAUSpider):
    name = "dominos_pizza_fr"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    allowed_domains = ["dominos.fr"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        for city in city_locations("FR", 15000):
            yield JsonRequest(
                url=f"https://www.dominos.fr/dynamicstoresearchapi/getstoresfromquery?lon={city['longitude']}&lat={city['latitude']}",
            )
