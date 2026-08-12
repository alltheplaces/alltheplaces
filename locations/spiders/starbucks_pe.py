from typing import AsyncIterator

from scrapy.http import JsonRequest

from locations.geo import city_locations
from locations.spiders.starbucks_us import API_SERVER_REACH_MILES, HEADERS, STORELOCATOR, StarbucksUSSpider


class StarbucksPESpider(StarbucksUSSpider):
    name = "starbucks_pe"
    item_attributes = StarbucksUSSpider.item_attributes
    country_filter = ["PE"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        for city in city_locations("PE", 15000):
            yield JsonRequest(
                url=STORELOCATOR.format(city["latitude"], city["longitude"]),
                headers=HEADERS,
                meta={"half_width_miles": API_SERVER_REACH_MILES, "depth_level": 0},
            )
