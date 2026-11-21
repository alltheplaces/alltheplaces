import re
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature

SOCKETS = {"type_2_plug": "type2", "ccs": "type2_combo", "chademo": "chademo"}


class ChargePlaceScotlandGBSpider(Spider):
    name = "charge_place_scotland_gb"
    item_attributes = {"operator": "ChargePlace Scotland", "operator_wikidata": "Q105359316"}
    start_urls = ["https://chargeplacescotland.org/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        token = re.search(r"apiAuthKey: '(\w+)',", response.text).group(1)
        yield JsonRequest(
            url="https://account.chargeplacescotland.org/api/v3/poi/chargepoint/static",
            headers={"api-auth": token},
            callback=self.parse_api,
        )

    def parse_api(self, response: Response, **kwargs: Any) -> Any:
        sites = {}
        for location in response.json()["features"]:
            sites.setdefault(location["properties"]["siteID"], []).append(self.parse_charge_point(location))

        for site_id, charge_points in sites.items():
            yield self.parse_charging_station(site_id, charge_points)
            yield from charge_points

    def parse_charge_point(self, location: dict) -> Feature:
        item = DictParser.parse(location["properties"])
        # Yep this is GeoJson, yep they have it the wrong way around
        item["lat"], item["lon"] = location["geometry"]["coordinates"]
        item["name"] = location["properties"]["address"]["sitename"]
        item["image"] = location["properties"]["imageUrl"]
        item["website"] = f'https://chargeplacescotland.org/cpmap/chargepoint/{item["ref"]}/'
        if location["properties"]["tariff"]["amount"] and location["properties"]["tariff"]["currency"]:
            item["extras"]["charge"] = "{} {}/kWh".format(
                location["properties"]["tariff"]["amount"], location["properties"]["tariff"]["currency"]
            )
        sockets = {}
        for group in location["properties"]["connectorGroups"] or []:
            for connector in group["connectors"]:
                if socket := SOCKETS.get(connector["connectorPlugType"]):
                    count, output = sockets.get(socket, (0, 0))
                    sockets[socket] = (count + 1, max(output, float(connector["connectorMaxChargeRate"])))
        for socket, (count, output) in sockets.items():
            item["extras"][f"socket:{socket}"] = str(count)
            item["extras"][f"socket:{socket}:output"] = f"{output:g} kW"

        apply_category(Categories.CHARGE_POINT, item)

        return item

    def parse_charging_station(self, site_id: str, charge_points: list[Feature]) -> Feature:
        first = charge_points[0]
        station = Feature(ref=site_id, lat=first["lat"], lon=first["lon"], name=first["name"])
        for key in ("housenumber", "street", "street_address", "city", "state", "postcode", "country"):
            if first.get(key):
                station[key] = first[key]
        station["extras"]["capacity"] = str(len(charge_points))
        for socket in SOCKETS.values():
            counts = [
                int(cp["extras"][f"socket:{socket}"]) for cp in charge_points if f"socket:{socket}" in cp["extras"]
            ]
            if counts:
                outputs = [
                    float(cp["extras"][f"socket:{socket}:output"].removesuffix(" kW"))
                    for cp in charge_points
                    if f"socket:{socket}" in cp["extras"]
                ]
                station["extras"][f"socket:{socket}"] = str(sum(counts))
                station["extras"][f"socket:{socket}:output"] = f"{max(outputs):g} kW"

        apply_category(Categories.CHARGING_STATION, station)

        return station
