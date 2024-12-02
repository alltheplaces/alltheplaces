from typing import Any, Iterable

import scrapy
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.items import Feature


class BrillenDESpider(scrapy.Spider):

    name = "brillen_de"
    item_attributes = {"brand": "brillen.de", "brand_wikidata": "Q105275794"}

    def start_requests(self):
        for lat, lon in point_locations("eu_centroids_40km_radius_country.csv", "DE"):
            # The api has some unknown maximum radius and doesn't respect
            # arbitrarily large radius values, so we use a latlng grid
            yield JsonRequest(
                f"https://cal.supervista.de/public/store/nearby?longitude={lon}&latitude={lat}&radius=99999999&unit=km&limit=10000",
                headers={"X-Country-Code": "de"},
            )

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.json()["data"]["stores"]:

            # They also have "normal" opticians as partner stores. We're only
            # interested in their own branded shops.
            if location["store_name"].startswith("brillen.de"):
                location["name"] = location.pop("store_name")
                location["ref"] = location.pop("store_id")
                location["postcode"] = location.pop("zip")
                location["street_address"] = location.pop("street")
                location["country"] = "DE"
                item = DictParser.parse(location)

                yield item
