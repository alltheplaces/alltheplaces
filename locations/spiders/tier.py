from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.items import Feature


class TierSpider(Spider):
    name = "tier"
    item_attributes = {"name": "Tier", "operator": "Tier", "operator_wikidata": "Q63386916"}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            "https://platform.tier-services.io/v1/zone",
            headers={"X-Api-Key": "bpEUTJEBTf74oGRWxaIcW7aeZMzDDODe1yBoSxi2"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            if location["attributes"]["zoneType"] != "parking":
                continue

            item = Feature()
            item["ref"] = location["id"]
            # Names are bad in most zones
            # item["name"] = location["attributes"]["name"]

            item["lat"] = location["attributes"]["lat"]
            item["lon"] = location["attributes"]["lng"]
            item["country"] = location["attributes"]["country"]

            # TODO: we could do with the vehicles types, then add OSM tags
            # eg amenity=bicycle_rental, amenity=kick-scooter_rental, amenity=motorcycle_rental, amenity=car_rental
            # but until then, we can do a white lie and call it public transit
            item["extras"]["public_transport"] = "stop_position"

            yield item
