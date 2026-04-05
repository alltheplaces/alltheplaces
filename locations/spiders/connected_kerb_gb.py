from locations.categories import Categories, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

SOCKET_TYPES = {
    "CHAdeMO": "chademo",
    "IEC_62196_T2_COMBO": "type2_combo",
    "Type 2": "type2",
}


class ConnectedKerbGBSpider(JSONBlobSpider):
    name = "connected_kerb_gb"
    item_attributes = {
        "operator": "Connected Kerb",
        "operator_wikidata": "Q113579669",
    }
    start_urls = ["https://connectedkerb.com/umbraco/api/maps/data/en-GB"]

    def post_process_item(self, station_item, response, station_location):
        station_item["street_address"] = station_item.pop("addr_full")
        station_item["website"] = station_location["yextLink"]["href"]

        for connector_type in (
            station_location["connectorType"].removeprefix("Plug type: ").removeprefix("Plug types: ").split(", ")
        ):
            if connector_type in SOCKET_TYPES:
                socket_type = SOCKET_TYPES[connector_type]
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/unhandled_socket_type/{connector_type}")
                socket_type = "unknown"
            apply_yes_no(f"socket:{socket_type}", station_item, True)
            station_item["extras"][f"socket:{socket_type}:output"] = station_location["maxSpeed"].removeprefix(
                "Max speed: "
            )

        apply_category(Categories.CHARGING_STATION, station_item)
        yield station_item

        for i, point_location in enumerate(station_location["chargingPoints"]):
            point_item = Feature(lat=station_item["lat"], lon=station_item["lon"])
            point_item["ref"] = point_location.get("socketId", f"{station_item['ref']}:{i}")
            if point_location["type"] in SOCKET_TYPES:
                socket_type = SOCKET_TYPES[point_location["type"]]
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/unhandled_socket_type/{point_location['type']}")
                socket_type = "unknown"
            apply_yes_no(f"socket:{socket_type}", point_item, True)
            point_item["extras"][f"socket:{socket_type}:output"] = point_location["maxPower"]

            apply_category({"man_made": "charge_point"}, point_item)
            yield point_item
