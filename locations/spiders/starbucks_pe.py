from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, Response

from locations.geo import city_locations
from locations.items import Feature
from locations.spiders.starbucks_us import API_SERVER_REACH_MILES, HEADERS, STORELOCATOR, StarbucksUSSpider


class StarbucksPESpider(StarbucksUSSpider):
    name = "starbucks_pe"
    item_attributes = StarbucksUSSpider.item_attributes
    country_filter = ["PE"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        # Nearby cities see the same stores, so only seed cities outside the reach of
        # every already-seeded (more populous) city; subdivision covers the rest.
        seeds: list[dict] = []
        for city in sorted(city_locations("PE", 15000), key=lambda c: c["population"], reverse=True):
            if any(
                self._miles_between(city["latitude"], city["longitude"], seed["latitude"], seed["longitude"])
                < API_SERVER_REACH_MILES
                for seed in seeds
            ):
                continue
            seeds.append(city)
            yield JsonRequest(
                url=STORELOCATOR.format(city["latitude"], city["longitude"]),
                headers=HEADERS,
                meta={"half_width_miles": API_SERVER_REACH_MILES, "depth_level": 0},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for result in super().parse(response, **kwargs):
            if isinstance(result, Feature):
                result["phone"] = None
            yield result
