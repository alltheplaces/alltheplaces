from typing import Any
from urllib.parse import urlencode

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class ChargeUpSpider(scrapy.Spider):
    start_urls = [
        "https://app.chargeup.cz/chargingPlace/listNearest?criteria.powerFrom=0&criteria.dataSources%5B0%5D=chargeup&criteria.onlyAvailable=false&midpoint.lat=0&midpoint.lng=0&fastCountTotal=true&pageInfo.pageIndex=0&pageInfo.pageSize=10000"
    ]
    name = "charge_up"
    item_attributes = {"brand": "ChargeUp", "brand_wikidata": "Q109066768"}
    providers = {
        "5e552d126f3f9d0027287349": ["HAVEX-auto", None],
        "5e66498bf8c88b0027e2f333": ["Teplárny Brno", "Q54980987"],
        "5f3393747bf4b90027b1cdb3": ["AUTOS Kunštát", None],
        "5f35081e7bf4b90027b6a5de": ["EURO CAR Zlín", None],
        "60532e0b80a51f00294f43d2": ["Transfer Energy", None],
        "607eb1dfb7923e0029b05049": ["TotalEnergies", "Q154037"],
        "6188ee27a05b8a002d08fe34": ["Vitesco Technologies", "Q98703020"],
        "61892b0ea05b8a002d098d8d": ["EWE", "Q53199345"],
        "641d52482336420040dde9db": ["ChargeUp", "Q109066768"],
    }
    connectors = {
        "CHAdeMO": "chademo",
        "Mennekes": "type2",
        "CCS1": "type1_combo",
        "CCS2": "type2_combo",
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        result = response.json()

        for stations in result["chargingPlaces"]:
            for station in stations["chargingStations"]:
                if station["state"] != "VALID":
                    continue

                yield JsonRequest(
                    url="https://app.chargeup.cz/chargingPlace/getStation?%s"
                    % (urlencode({"stationCode": station["stationCode"]})),
                    callback=self.parse_station,
                )

    def parse_station(self, response: Response, **kwargs: Any) -> Any:
        result = response.json()
        station = result["chargingStation"]
        item = Feature()

        evse = [evseId for point in station["chargingPoints"] if (evseId := point["evseId"]) is not None]
        evse.sort()
        connectors = {}
        for connector in [point["connectors"]["types"][0] for point in station["chargingPoints"]]:
            if not connector["key"] in connectors:
                connectors[connector["key"]] = []
            connectors[connector["key"]].append(
                str(connector["maxPower"]["energy"]) + " " + connector["maxPower"]["unit"]
            )

            if connector["caption"].startswith("Mennekes 3x"):
                item["extras"]["socket:type2:voltage"] = "400"

        item["name"] = station["name"].strip()
        item["lon"] = station["location"]["coordinates"][0]
        item["lat"] = station["location"]["coordinates"][1]
        item["ref"] = station["stationCode"]
        if evse:
            item["extras"]["ref:EU:EVSE"] = ";".join(evse)

        for k in connectors:
            tag = self.connectors[k]
            item["extras"][("socket:%s") % tag] = str(len(connectors[k]))
            item["extras"][("socket:%s:output") % tag] = ";".join(sorted(set(connectors[k])))

        # A bit of guessing
        item["extras"]["capacity"] = str(max([len(connector) for connector in connectors.values()]))

        providerId = result["providerId"]
        if providerId in self.providers:
            provider = self.providers[result["providerId"]]
            item["operator"] = provider[0]
            if provider[1]:
                item["operator_wikidata"] = provider[1]
        item["extras"]["ref:operator"] = providerId

        item["website"] = ("https://app.chargeup.cz/map?%s") % (urlencode({"stationCode": station["stationCode"]}))

        address = station["address"]
        item["street_address"] = address["street"].strip()
        if address["orientationNumber"]:
            item["housenumber"] = address["orientationNumber"].strip()
        elif address["descriptiveNumber"]:
            item["housenumber"] = address["descriptiveNumber"].strip()
        item["city"] = address["city"].strip()
        if address["postalCode"]:
            item["postcode"] = address["postalCode"].strip()
        item["country"] = address["country"].strip()
        item["addr_full"] = station["derivedAddress"].strip()

        item["extras"]["access"] = "yes" if station["isPublic"] else "private"

        charge = []
        for point in station["chargingPoints"]:
            if point["priceForEnergy"] and point["priceForEnergy"]["price"] > 0:
                charge.append(
                    ("%s %s/%s")
                    % (
                        point["priceForEnergy"]["price"],
                        point["priceForEnergy"]["currency"],
                        point["priceForEnergy"]["unit"],
                    )
                )
            if point["priceForChargingTime"] and point["priceForChargingTime"]["price"] > 0:
                charge.append(
                    ("%s %s/%s")
                    % (
                        point["priceForChargingTime"]["price"],
                        point["priceForChargingTime"]["currency"],
                        point["priceForChargingTime"]["unit"],
                    )
                )
        if charge:
            item["extras"]["fee"] = "yes"
            item["extras"]["charge"] = ";".join(sorted(set(charge)))

        if "chargingStationImages" in station and station["chargingStationImages"]:
            for image in station["chargingStationImages"]:
                if "id" in image:
                    item["image"] = ("https://app.chargeup.cz/portal/getImage?%s") % (
                        urlencode({"id": image["id"], "providerId": result["providerId"]})
                    )

        phone = [phone for point in station["chargingPoints"] if (phone := point["techSupportPhoneNumber"]) is not None]
        item["phone"] = ";".join(sorted(set(phone)))

        apply_category(Categories.CHARGING_STATION, item)

        yield item
