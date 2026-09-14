from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.items import Feature


class AedLocationsNZSpider(Spider):
    name = "aed_locations_nz"
    item_attributes = {"country": "NZ"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://mapmysites.com/api/aed/locations/viewport.geojson?bounds=-90,-180,90,180",
            callback=self.parse,
        )

    def parse(self, response):
        for feature in response.json()["features"]:
            props = feature["properties"]
            coords = feature["geometry"]["coordinates"]

            item = Feature()
            item["ref"] = props["id"]
            item["name"] = props.get("name")
            item["addr_full"] = props.get("physical_address")
            item["lon"] = coords[0]
            item["lat"] = coords[1]

            if props.get("available_24_7"):
                item["opening_hours"] = "24/7"

            apply_category(Categories.DEFIBRILLATOR, item)
            yield item
