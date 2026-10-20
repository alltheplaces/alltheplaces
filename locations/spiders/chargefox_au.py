from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# Chargefox's GraphQL "typeName" plug values mapped to OSM socket:* keys.
PLUGS = {
    "sae_j1772": "type1",
    "iec_62196_type2": "type2",
    "ccs_combo1": "type1_combo",
    "ccs_combo2": "type2_combo",
    "chademo": "chademo",
}


class ChargefoxAUSpider(Spider):
    name = "chargefox_au"
    item_attributes = {"name": "Chargefox", "operator": "Chargefox", "operator_wikidata": "Q105775824"}
    graphql_url = "https://app.chargefox.com/graphql"
    # Chargefox answers per-location detail queries batched together as GraphQL aliases,
    # which is far fewer requests than querying every location one at a time.
    batch_size = 25

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=self.graphql_url,
            data={
                "variables": {"sw": {"lat": -51.66, "lng": 100.09}, "ne": {"lat": -0.69, "lng": 166.74}},
                "query": (
                    "query Locations($sw: GeoLocationInput!, $ne: GeoLocationInput!) "
                    "{ locationsByBounds(sw: $sw, ne: $ne) { id lat lng planned } }"
                ),
            },
            callback=self.parse_locations,
        )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        locations = {loc["id"]: loc for loc in response.json()["data"]["locationsByBounds"] if not loc["planned"]}
        location_ids = list(locations.keys())

        for offset in range(0, len(location_ids), self.batch_size):
            batch_ids = location_ids[offset : offset + self.batch_size]
            variables = {f"id{n}": loc_id for n, loc_id in enumerate(batch_ids)}
            variable_defs = ", ".join(f"$id{n}: ID!" for n in range(len(batch_ids)))
            aliases = "\n".join(
                f"loc{n}: location(id: $id{n}) {{ name maxPower "
                "chargeStations { connectors { plug { typeName } } } }"
                for n in range(len(batch_ids))
            )
            yield JsonRequest(
                url=self.graphql_url,
                data={"variables": variables, "query": f"query LocationBatch({variable_defs}) {{ {aliases} }}"},
                callback=self.parse_details,
                cb_kwargs={"batch_locations": {loc_id: locations[loc_id] for loc_id in batch_ids}},
            )

    def parse_details(self, response: Response, batch_locations: dict, **kwargs: Any) -> Any:
        data = response.json()["data"]
        for n, (loc_id, location) in enumerate(batch_locations.items()):
            detail = data.get(f"loc{n}")
            if not detail:
                continue

            item = Feature()
            item["ref"] = loc_id
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]
            item["branch"] = detail["name"]

            socket_counts: dict[str, int] = {}
            for station in detail["chargeStations"]:
                for connector in station["connectors"]:
                    type_name = (connector.get("plug") or {}).get("typeName")
                    if osm_socket := PLUGS.get(type_name):
                        socket_counts[osm_socket] = socket_counts.get(osm_socket, 0) + 1
                    else:
                        self.logger.warning("Unknown plug type: {}".format(type_name))

            if total := sum(socket_counts.values()):
                item["extras"]["capacity"] = str(total)
            for osm_socket, count in socket_counts.items():
                item["extras"][f"socket:{osm_socket}"] = str(count)
                if max_power := detail.get("maxPower"):
                    item["extras"][f"socket:{osm_socket}:output"] = f"{float(max_power):g} kW"

            apply_category(Categories.CHARGING_STATION, item)

            yield item
