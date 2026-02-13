from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class AedLocationsNZSpider(Spider):
    name = "aed_locations_nz"
    item_attributes = {}
    allowed_domains = ["mapmysites.com"]
    start_urls = ["https://mapmysites.com/api/aed/locations/viewport.geojson?bounds=-90,-180,90,180"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.parse)

    def parse(self, response):
        for location_simple in response.json()["features"]:
            yield JsonRequest(
                url=f"https://mapmysites.com/api/aed/locations/{location_simple['properties']['id']}.geojson",
                callback=self.parse_location,
            )

    def parse_location(self, response):
        location = response.json()

        item = DictParser.parse(location)
        item["ref"] = location["properties"]["id"]
        yield item
