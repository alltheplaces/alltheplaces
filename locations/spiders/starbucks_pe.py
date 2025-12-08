from scrapy.http import JsonRequest

from locations.geo import city_locations
from locations.spiders.starbucks_us import HEADERS, STORELOCATOR, StarbucksUSSpider


class StarbucksPESpider(StarbucksUSSpider):
    name = "starbucks_pe"
    item_attributes = StarbucksUSSpider.item_attributes
    country_filter = ["PE"]

    def start_requests(self):
        for city in city_locations("PE", 15000):
            yield JsonRequest(
                url=STORELOCATOR.format(city["latitude"], city["longitude"]),
                headers=HEADERS,
                meta={"distance": 1},
            )
