import json
import urllib.parse
from collections import defaultdict

from scrapy import Spider
from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser

SOCKET_TYPES = {
    1: "nema_5_20",  # unsure if nema_5_15 or nema_5_20
    3: "type1",
    39: "type1_combo",
    41: "chademo",
    51: "type1_combo",
    61: "chademo",
    77: "type1_combo",
    82: "type2",
    111: "nacs",
    121: "nacs",
    131: "nacs",
    215: "type1",
    227: "type2",
    231: "type2",
    241: "type1_combo",
    243: "type1_combo",
    247: "type1_combo",
    1249: "type1_combo",
    1257: "type1",
    1258: "type2",
    1259: "nacs",
    100053: "type1_combo",
    100054: "type1_combo",
    100067: "type2",
    100068: "nacs",
    100074: "type1_combo",
    100078: "type1_combo",
    100079: "type1_combo",
    100080: "type1_combo",
    100095: "type1_combo",
    100100: "type1",
    100102: "nacs",
    100105: "type1_combo",
    100107: "type1_combo",
    100131: "type1_combo",
    100151: "type1_combo",
    100190: "nacs",
    100200: "type1",
    100201: "type1",
    100203: "type1",
    100271: "type1",
    1000000025: "type2_cable",
    1000000035: "schuko",
    1000000045: "schuko",
    1000000065: "type2_cable",
    1000000095: "type1_combo",
    1000000105: "chademo",
    1000000225: "type1_combo",
    1000000235: "chademo",
    1000000285: "schuko",
    1000000325: "type2_cable",
    1000000435: "type2_cable",
    1000000495: "type2_cable",
    1000000595: "chademo",
    1000000615: "type2_combo",
    1000000665: "type1",
    1000000675: "type2_cable",
    1000000685: "type3",
}


class ChargepointSpider(Spider):
    name = "chargepoint"
    item_attributes = {"brand": "ChargePoint", "brand_wikidata": "Q5176149"}

    def make_request(self, query: dict, **kwargs) -> JsonRequest:
        return JsonRequest(
            url="https://mc.chargepoint.com/map-prod/v2?"
            + urllib.parse.quote(json.dumps(query, separators=(",", ":")).encode("utf-8")),
            **kwargs,
        )

    def make_map_data_request(self, bounds: dict) -> JsonRequest:
        return self.make_request(
            {"map_data": bounds | {"screen_width": 100, "screen_height": 100}}, callback=self.parse_map_data
        )

    def make_station_list_request(self, bounds: dict, page_offset: str = "") -> JsonRequest:
        return self.make_request(
            {
                "station_list": bounds
                | {"screen_width": 100, "screen_height": 100, "page_size": 50, "page_offset": page_offset}
            },
            callback=self.parse_station_list,
            cb_kwargs={"bounds": bounds},
        )

    async def start(self):
        yield self.make_map_data_request(
            {
                "sw_lon": -180.0,
                "sw_lat": -90.0,
                "ne_lon": 180.0,
                "ne_lat": 90.0,
            }
        )

    def parse_map_data(self, response):
        if "error" in response.json():
            self.logger.error(f"Server error from {response.url} : {response.json()['error']}")
            if "map_data" not in response.json():
                yield get_retry_request(
                    response.request,
                    spider=self,
                    reason=response.json()["error"],
                )

        map_data = response.json()["map_data"]

        if "error" in map_data:
            self.logger.error(f"Error in map_data from {response.url} :  {map_data['error']}")

        for blob in map_data.get("blobs", []):
            total_station_count = sum(blob["port_count"].values())
            if total_station_count <= 0:
                pass
            elif total_station_count < 1000:
                # If there are few enough stations to be covered by a paginated station_list request, use that
                yield self.make_station_list_request(blob["bounds"])
            else:
                # Otherwise, zoom in further
                yield self.make_map_data_request(blob["bounds"])

        for station in map_data.get("stations", []):
            yield self.parse_station_in_list(station)

    def parse_station_list(self, response, bounds: dict):
        if "error" in response.json():
            self.logger.error(f"Server error from {response.url} : {response.json()['error']}")
            if "station_list" not in response.json():
                yield get_retry_request(
                    response.request,
                    spider=self,
                    reason=response.json()["error"],
                )

        station_list = response.json()["station_list"]

        if "error" in station_list:
            self.logger.error(f"Error in station_list from {response.url} : {station_list['error']}")
            if "stations" not in station_list:
                yield get_retry_request(
                    response.request,
                    spider=self,
                    reason=station_list["error"],
                )

        if "page_offset" in station_list and station_list["page_offset"] != "last_page":
            yield self.make_station_list_request(bounds, station_list["page_offset"])

        for station in station_list.get("stations", []):
            yield self.parse_station_in_list(station)

    def parse_station_in_list(self, station: dict):
        item = DictParser.parse(station)

        item["name"] = " / ".join(filter(None, [station.get("name1"), station.get("name2")]))
        item["ref"] = station["device_id"]
        item["website"] = f"https://driver.chargepoint.com/stations/{station['device_id']}"
        item["extras"]["network"] = station["network_display_name"]
        item["extras"]["capacity"] = station["total_port_count"]

        if station.get("access_restriction", "NONE") != "NONE":
            item["extras"]["access"] = "private"

        apply_yes_no(
            Extras.WHEELCHAIR, item, station.get("parking_accessibility") in ("DISABLED_PARKING", "VAN_ACCESSIBLE")
        )
        apply_yes_no(Extras.FEE, item, station["payment_type"] == "paid", station["payment_type"] != "free")

        maxPowerPerSocket = defaultdict(float)
        for port in station["ports"]:
            if port["port_type"] in SOCKET_TYPES:
                socket_type = SOCKET_TYPES[port["port_type"]]
            else:
                self.logger.debug(f"On station {station['device_id']}: unknown socket type {port['port_type']}")
                self.crawler.stats.inc_value(f"atp/{self.name}/unhandled_socket_type/{port['port_type']}")
                socket_type = "unknown"
            apply_yes_no(f"socket:{socket_type}", item, True)
            if "available_power" in port:
                maxPowerPerSocket[socket_type] = max(maxPowerPerSocket[socket_type], float(port["available_power"]))
        for socket_type, max_power in maxPowerPerSocket.items():
            item["extras"][f"socket:{socket_type}:output"] = f"{max_power} kW"

        apply_category(Categories.CHARGE_POINT, item)

        return item
