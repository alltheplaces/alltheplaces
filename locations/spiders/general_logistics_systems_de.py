from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import OpeningHours


class GeneralLogisticsSystemsDESpider(Spider):
    name = "general_logistics_systems_de"
    allowed_domains = ["gls-pakete.de"]

    def start_requests(self):
        for latitude, longitude in point_locations("eu_centroids_40km_radius_country.csv", ["DE"]):
            yield JsonRequest(
                url="https://api.gls-pakete.de/parcelshops?latitude={:0.5}&longitude={:0.5}&distance=40".format(
                    latitude, longitude
                ),
                headers={"X-Requested-With": "XMLHttpRequest"},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for poi in response.json()["shops"]:
            item = DictParser.parse(poi)
            address = poi["address"]
            coordinates = address["coordinates"]
            item["lat"] = coordinates["latitude"]
            item["lon"] = coordinates["longitude"]
            item["name"] = address["name"]

            opening_hours = OpeningHours()
            for day, time_ranges in poi["openingHours"].items():
                for time_range in time_ranges:
                    opening_hours.add_range(day, time_range["from"], time_range["to"])
            item["opening_hours"] = opening_hours

            if "paketstation" in item["name"].lower():
                apply_category(Categories.PARCEL_LOCKER, item)
            else:
                apply_category(Categories.GENERIC_POI, item)
                item["extras"]["post_office"] = "post_partner"
                item["extras"]["post_office:brand"] = "GLS"

            yield item
