from typing import Any
from urllib.parse import urlencode

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class EmobilitaBrnoCzSpider(scrapy.Spider):
    name = "emobilita_brno_cz"
    item_attributes = {"operator": "Teplárny Brno", "operator_wikidata": "Q54980987"}

    def start_requests(self):
        yield JsonRequest(
            url="https://uuapp.plus4u.net/uu-chargeup-portalg01/cde72fa6c93d4cad87dcfd67ed8fc975/chargingPlace/listWithinPolygon",
            data={
                "criteria": {"connectors": [], "onlyAvailable": False, "dataSources": [], "powerFrom": 0},
                "northEast": {"lat": 90, "lng": 180},
                "southWest": {"lat": -90, "lng": -180},
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        result = response.json()

        for stations in result["chargingPlaces"]["itemList"]:
            for station in stations["chargingStations"]:
                if station["state"] != "VALID":
                    continue

                yield JsonRequest(
                    url="https://uuapp.plus4u.net/uu-chargeup-portalg01/cde72fa6c93d4cad87dcfd67ed8fc975/chargingPlace/getStation?%s"
                    % (urlencode({"stationCode": station["stationCode"]})),
                    callback=self.parse_station,
                )

    def parse_station(self, response: Response, **kwargs: Any) -> Any:
        result = response.json()
        station = result["chargingStation"]
        item = Feature()

        evse = [point["evseId"] for point in station["chargingPoints"]]
        evse.sort()
        connectors = {"Mennekes": [], "CCS2": []}
        for connector in [point["connectors"]["types"][0] for point in station["chargingPoints"]]:
            connectors[connector["key"]].append(
                str(connector["maxPower"]["energy"]) + " " + connector["maxPower"]["unit"]
            )

            if connector["caption"].startswith("Mennekes 3x"):
                item["extras"]["socket:type2:voltage"] = "400"

        item["name"] = station["name"]
        item["lon"] = station["location"]["coordinates"][0]
        item["lat"] = station["location"]["coordinates"][1]
        item["ref"] = station["stationCode"]
        item["extras"]["ref:EU:EVSE"] = ";".join(evse)

        if connectors["Mennekes"]:
            item["extras"]["socket:type2"] = str(len(connectors["Mennekes"]))
            item["extras"]["socket:type2:output"] = ";".join(set(connectors["Mennekes"]))

        if connectors["CCS2"]:
            item["extras"]["socket:type2_combo"] = str(len(connectors["CCS2"]))
            item["extras"]["socket:type2_combo:output"] = ";".join(set(connectors["CCS2"]))

        item["extras"]["capacity"] = str(max(len(connectors["Mennekes"]), len(connectors["CCS2"])))

        apply_category(Categories.CHARGING_STATION, item)

        yield item
