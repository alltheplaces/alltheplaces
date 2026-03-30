import json
import urllib.parse
from collections import defaultdict

from scrapy import Spider
from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


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
            {"map_data": bounds | {"screen_width": 9200, "screen_height": 9200}}, callback=self.parse_map_data
        )

    def make_station_list_request(self, bounds: dict, page_offset: str = "") -> JsonRequest:
        return self.make_request(
            {
                "station_list": bounds
                | {"screen_width": 9200, "screen_height": 9200, "page_size": 50, "page_offset": page_offset}
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

        if station_list["page_offset"] != "last_page":
            yield self.make_station_list_request(bounds, station_list["page_offset"])

        for station in station_list.get("stations", []):
            yield self.parse_station_in_list(station)

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
            elif total_station_count < 100000:
                # If there are few enough stations to be covered by a paginated station_list request, use that
                yield self.make_station_list_request(blob["bounds"])
            else:
                # Otherwise, zoom in further
                yield self.make_map_data_request(blob["bounds"])

        for station in map_data.get("stations", []):
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
            socket_type = port["port_type"]
            apply_yes_no(f"socket:{socket_type}", item, True)
            if "available_power" in port:
                maxPowerPerSocket[socket_type] = max(maxPowerPerSocket[socket_type], float(port["available_power"]))
        for socket_type, max_power in maxPowerPerSocket.items():
            item["extras"][f"socket:{socket_type}:output"] = f"{max_power} kW"

        apply_category(Categories.CHARGE_POINT, item)

        return item
