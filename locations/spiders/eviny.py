from typing import Iterable

from scrapy import Spider
from scrapy.http import TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature

SOCKET_TYPE_MAPPING = {
    "CCS": "type2_combo",
    "CHAdeMO": "chademo",
    "AC Type 2": "type2",
}

AMENITY_MAPPING = {
    "RESTROOM": Extras.TOILETS,
    "WIFI": Extras.WIFI,
    "CAR_TRAILER": Extras.CARAVAN_SITES,
    "BAR": Extras.BAR,
}


class EvinySpider(Spider):
    name = "eviny"
    item_attributes = {"brand": "Eviny", "brand_wikidata": "Q4891601"}
    start_urls = ["https://hurtiglading.eviny.no/api/map/chargingStations"]

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for charger in response.json().get("chargingStations", []):
            item = DictParser.parse(charger)

            item["branch"] = item.pop("name")

            if description := charger.get("description"):
                item["extras"]["description"] = description

            item["extras"]["capacity"] = charger.get("totalConnectors")

            self._parse_sockets(charger.get("connectionsTypes", {}), item)
            self._parse_amenities(charger.get("amenities", []), item)

            apply_category(Categories.CHARGING_STATION, item)
            yield item

    def _parse_sockets(self, connections_types: dict, item: Feature) -> None:
        for socket_name, osm_socket in SOCKET_TYPE_MAPPING.items():
            connectors = connections_types.get(socket_name, [])
            if connectors:
                item["extras"][f"socket:{osm_socket}"] = len(connectors)
                max_output = max(c.get("effect", 0) for c in connectors)
                if max_output:
                    item["extras"][f"socket:{osm_socket}:output"] = f"{max_output} kW"

    def _parse_amenities(self, amenities: list, item: Feature) -> None:
        for amenity in amenities:
            if tag := AMENITY_MAPPING.get(amenity):
                apply_yes_no(tag, item, True)
