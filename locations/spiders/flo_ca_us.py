from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.geo import make_subdivisions
from locations.items import Feature

SOCKET_TYPES = {
    "CHADEMO": "chademo",
    "IEC_62196_T1": "type1",
    "IEC_62196_T1_COMBO": "type1_combo",
    "IEC_62196_T2": "type2",
    "IEC_62196_T2_COMBO": "type2_combo",
    "J3400": "nacs",
    "TESLA_S": "nacs",
}


class FloCAUSSpider(Spider):
    name = "flo_ca_us"
    item_attributes = {
        "brand": "FLO",
        "brand_wikidata": "Q64971203",
        "operator": "FLO",
        "operator_wikidata": "Q64971203",
    }

    def make_request(self, zoom_level: int, bounds: tuple[float, float, float, float]) -> JsonRequest:
        return JsonRequest(
            "https://emobility.flo.ca/v3.0/map/markers/search",
            data={
                "bounds": {
                    "SouthWest": {"Latitude": bounds[1], "Longitude": bounds[0]},
                    "NorthEast": {"Latitude": bounds[3], "Longitude": bounds[2]},
                },
                "filter": {"networkIds": [1, 6]},
                "zoomLevel": zoom_level,
            },
            cb_kwargs={"zoom_level": zoom_level, "bounds": bounds},
        )

    async def start(self):
        yield self.make_request(zoom_level=0, bounds=(-180, -85, 180, 85))

    def parse(self, response, zoom_level, bounds):
        for park in response.json()["parks"]:
            station = self.parse_station(park)
            yield station
            for point in park["stations"]:
                yield self.parse_charge_point(station, point)

        clusters = response.json()["clusters"]
        for subdivision in make_subdivisions(bounds, 2):
            xmin, ymin, xmax, ymax = subdivision
            if (
                any(
                    xmin <= cluster["geoCoordinates"]["longitude"] < xmax
                    and ymin <= cluster["geoCoordinates"]["latitude"] < ymax
                    for cluster in clusters
                )
                > 0
            ):
                yield self.make_request(zoom_level=zoom_level + 1, bounds=subdivision)

    def parse_station(self, location) -> Feature:
        item = Feature(
            ref=location["id"],
            name=location["name"],
            lat=location["geoCoordinates"]["latitude"],
            lon=location["geoCoordinates"]["longitude"],
        )
        apply_category(Categories.CHARGING_STATION, item)
        return item

    def parse_charge_point(self, parent: Feature, location: dict) -> Feature:
        item = Feature(
            lat=parent["lat"],
            lon=parent["lon"],
            ref=f"{parent['ref']}:{location['id']}",
            name=location["name"],
        )
        apply_yes_no(Extras.FEE, item, not location.get("freeOfCharge", False), "freeOfCharge" not in location)

        for connector in location["connectors"]:
            if connector in SOCKET_TYPES:
                socket_type = SOCKET_TYPES[connector]
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/unhandled_socket_type/{connector}")
                socket_type = "unknown"
            apply_yes_no(f"socket:{socket_type}", item, True)
            item["extras"][f"socket:{socket_type}:output"] = f"{location['chargingSpeed']} kW"

        apply_category(Categories.CHARGE_POINT, item)
        return item
