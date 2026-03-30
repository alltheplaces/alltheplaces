import json
import urllib.parse
from collections import defaultdict

from scrapy import Spider
from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature, set_closed

SOCKET_TYPES = {
    "CCS1": "type1_combo",
    "CCS2": "type2_combo",
    "CHAdeMO": "chademo",
    "CHAdeMO / Combo": "chademo_combo",  # ???
    "Combo": "type1_combo",
    "DOMESTIC-E": "typee",
    "J1772": "type1",
    "Mennekes": "type2",
    "MennekesCOMBO": "type2_combo",
    "NACS - Adapter": "nacs",
    "NACS (Tesla)": "nacs",
    "Schuko": "schuko",
    "Type 1": "type1",
    "Type 2 Cable": "type2_cable",
    "Type 2 Socket": "type2",
    "Type 2": "type2_cable",
    "Type 3 Socket": "type3",
    "Type 3": "type3",
    "Type E": "typee",
    "Wall Outlet": "domestic",
}
UNITS = {
    "HOUR": "hour",
    "KWH": "kWh",
    "MINUTE": "minute",
}


def convertFixedFee(price: dict, fee: dict) -> str:
    if fee["unit"] == "SESSION":
        return f"{fee['amount']} {price['currencyCode']}"
    else:
        return f"{fee['amount']} {price['currencyCode']}/{UNITS[fee['unit']]}"


def convertTime(t: int) -> str:
    return f"{t//3600:02}:{(t//60)%60:02}"


def convertTouFeeList(price: dict, dayFees: list) -> str:
    charges = []
    for dayFee in dayFees:
        day = {
            "mon": "Mo ",
            "tue": "Tu ",
            "wed": "We ",
            "thu": "Th ",
            "fri": "Fr ",
            "sat": "Sa ",
            "sun": "Su ",
            "alldays": "",
        }[dayFee["day"]]
        charges.append(
            f"{convertFixedFee(price, dayFee['fee'])} @ {day}{convertTime(dayFee['startTime'])}-{convertTime(dayFee['endTime'])}"
        )
    return "; ".join(charges)


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
        return self.make_request({"map_data": bounds | {"screen_width": 9200, "screen_height": 9200}}, callback=self.parse_map_data)

    def make_station_list_request(self, bounds: dict, page_offset: str="", **cb_kwargs) -> JsonRequest:
        return self.make_request({"station_list": bounds | {"screen_width": 9200, "screen_height": 9200, "page_size": 50, "page_offset": page_offset}}, callback=self.parse_station_list, cb_kwargs={"bounds": bounds, **cb_kwargs})

    async def start(self):
        yield self.make_map_data_request({
            "sw_lon": -180.0,
            "sw_lat": -90.0,
            "ne_lon": 180.0,
            "ne_lat": 90.0,
        })

    def parse_station_list(self, response, bounds: dict, page=1, total_count=0, expected_count=None):
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
            raise ValueError(f"Error in station_list from {response.url} : {station_list['error']}")
            if "stations" not in station_list:
                yield get_retry_request(
                    response.request,
                    spider=self,
                    reason=station_list["error"],
                )

        total_count += len(station_list.get("stations", []))

        if station_list["page_offset"] != "last_page":
            yield self.make_station_list_request(bounds, station_list["page_offset"], page=page+1, total_count=total_count, expected_count=expected_count)

        if expected_count is not None and "stations" in station_list and total_count+50 < expected_count and station_list["page_offset"] == "last_page":
            self.logger.error(f"From {response.url} : Reached end of station list after {page} pages before reaching expected number of stations ({total_count} vs {expected_count}). Decrease the station list threshold")

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
                yield self.make_station_list_request(blob["bounds"], expected_count=total_station_count)
            else:
                # Otherwise, zoom in further
                yield self.make_map_data_request(blob["bounds"])

        for station in map_data.get("stations", []):
            # Start with the station information we have in this request
            yield self.parse_station_in_list(station)
            # Also queue a low-priority request to get more detailed information
            #yield JsonRequest(
            #    f"https://mc.chargepoint.com/map-prod/v3/station/info?deviceId={station['device_id']}",
            #    callback=self.parse_standalone_station,
            #    priority=-1,
            #)

    def convertFee(self, price: dict, fee: dict, item: Feature) -> None:
        if "durationBasedFee" in fee:
            durationBasedFee = fee["durationBasedFee"]
            item["extras"][
                "charge:conditional"
            ] = f"{durationBasedFee['initialFee']['amount']} {price['currencyCode']} @ stay < {durationBasedFee['initialFee']['duration'] / 3600} hours"
            item["extras"]["charge"] = f"{durationBasedFee['nextFee']['amount']} {price['currencyCode']}"
        elif "fixedFee" in fee:
            item["extras"]["charge"] = convertFixedFee(price, fee["fixedFee"])
        elif "touFeeList" in fee:
            item["extras"]["charge:conditional"] = convertTouFeeList(price, fee["touFeeList"])
        elif "chargingBasedFee" in fee:
            if "whileNotCharging" in fee:
                item["extras"]["charge"] = convertFixedFee(price, fee["whileNotCharging"])
            if "whileCharging" in fee:
                item["extras"]["charge:conditional"] = f'{convertFixedFee(price, fee["whileCharging"])} @ "charging"'
        else:
            self.logger.error(f"No supported fee scheme found on station {item['ref']}, available: {fee.keys()}")

    def getSocketType(self, connector: dict) -> str:
        if connector["displayPlugType"] in SOCKET_TYPES:
            return SOCKET_TYPES[connector["displayPlugType"]]
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unhandled_socket_type/{connector['displayPlugType']}")
            return "unknown"

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

    def parse_standalone_station(self, response):
        station = response.json()
        item = DictParser.parse(station)

        item["name"] = " / ".join(filter(None, station.get("name", [])))
        item["ref"] = station["deviceId"]
        item["website"] = f"https://driver.chargepoint.com/stations/{station['deviceId']}"
        item["extras"]["model"] = station.get("modelNumber")
        item["extras"]["network"] = station["network"]["displayName"]
        item["operator"] = station["hostName"]
        item["extras"]["capacity"] = station["portsInfo"]["portCount"]

        if station.get("accessRestriction", "NONE") != "NONE":
            item["extras"]["access"] = "private"

        apply_yes_no(
            Extras.WHEELCHAIR, item, station.get("parkingAccessibility") in ("DISABLED_PARKING", "VAN_ACCESSIBLE")
        )

        maxPowerPerSocket = defaultdict(float)
        for port in station["portsInfo"].get("ports", []):
            if "powerRange" in port and port["powerRange"]["unit"] != "kW":
                self.logger.error(f"Unexpected power unit {port['powerRange']['unit']} on station {station['deviceId']}")
                continue
            for connector in port["connectorList"]:
                socket_type = self.getSocketType(connector)
                apply_yes_no(f"socket:{socket_type}", item, True)
                if "powerRange" in port:
                    maxPowerPerSocket[socket_type] = max(maxPowerPerSocket[socket_type], float(port["powerRange"]["max"]))
        for socket_type, max_power in maxPowerPerSocket.items():
            item["extras"][f"socket:{socket_type}:output"] = f"{max_power} kW"
        for connector in station["portsInfo"].get("sitePortInfoList", []):
            socket_type = self.getSocketType(connector)
            apply_yes_no(f"socket:{socket_type}", item, True)

        if "stationPrice" in station:
            price = station["stationPrice"]
            apply_yes_no(Extras.FEE, item, not price.get("free", False), False)
            if not price.get("free", False) and "currencyCode" in price:
                if "energyFee" in price:
                    convertFee(price, price["energyFee"], item)
                elif "parkingFee" in price:
                    convertFee(price, price["parkingFee"], item)
                elif "flatFee" in price:
                    item["extras"]["charge"] = convertFixedFee(price, price["flatFee"])
                else:
                    self.logger.error(f"No supported pricing scheme found on station {station['deviceId']}; available: {price.keys()}")

        apply_category(Categories.CHARGE_POINT, item)

        yield item
