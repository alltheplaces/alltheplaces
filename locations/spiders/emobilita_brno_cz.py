from typing import Any

import scrapy
from scrapy.http import JsonRequest, Response

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

                evse = [point["evseId"] for point in station["chargingPoints"]]
                connectors = [point["connectors"]["types"][0]["key"] for point in station["chargingPoints"]]
                mennekes = connectors.count("Mennekes")
                ccs2 = connectors.count("CCS2")

                item = Feature()
                item["name"] = station["name"]
                item["lon"] = station["location"]["coordinates"][0]
                item["lat"] = station["location"]["coordinates"][1]
                item["ref"] = station["stationCode"]
                item["extras"]["ref:EU:EVSE"] = ";".join(evse)
                if mennekes:
                    item["extras"]["socket:type2"] = str(mennekes)
                if ccs2:
                    item["extras"]["socket:type2_combo"] = str(ccs2)
                item["extras"]["capacity"] = str(max(mennekes, ccs2))

                yield item
