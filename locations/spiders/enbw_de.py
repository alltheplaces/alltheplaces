import re
from typing import Any, AsyncIterator
from urllib.parse import urlencode

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser

# Maps the EnBW connector code to an OSM socket key, but only used when a
# station has exactly one plug type, since the API only gives a combined
# charge point count and doesn't break it down per connector type.
SOCKET_TYPES = {
    "TYPE_2": "type2",
    "CCS": "type2_combo",
    "CHADEMO": "chademo",
}

ADDRESS_RE = re.compile(r"^(?P<street>.+?),\s*(?P<postcode>\d{4,5})\s+(?P<city>.+?),\s*(?P<country>[A-Z]{2})$")


class EnbwDESpider(Spider):
    name = "enbw_de"
    # NSI lists this operator string/QID (EnBW's e-mobility subsidiary) specifically for
    # amenity=charging_station, distinct from the parent EnBW group (Q644304).
    item_attributes = {"operator": "EnBW mobility+ AG und Co.KG", "operator_wikidata": "Q124738664"}

    # The public charging map at enbw.com/elektromobilitaet/unterwegs-laden calls this API
    # with a map viewport bounding box. It covers the whole EnBW HyperNetz (EnBW's own
    # chargers plus thousands of EU roaming partners), so `operator=EnBW` is used to keep
    # only EnBW's own charging stations, which are all located in Germany.
    # The subscription key below is the one this public page itself uses in every browser
    # request (not a private credential); EnBW may rotate it without notice.
    API = "https://api.emp.emob-enbw.com/emobility-public-api/api/v1/chargestations"
    API_KEY = "90a67b9900364009b588e100e4b1cc64"
    COUNTRY_BBOX = (47.2, 5.5, 55.1, 15.5)  # (from_lat, from_lon, to_lat, to_lon) covering Germany
    MIN_SPAN = 0.01  # stop subdividing below this span (degrees) to guarantee termination

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self._cell_request(self.COUNTRY_BBOX)

    def _cell_request(self, bbox: tuple[float, float, float, float]) -> JsonRequest:
        from_lat, from_lon, to_lat, to_lon = bbox
        params = {
            "fromLat": from_lat,
            "toLat": to_lat,
            "fromLon": from_lon,
            "toLon": to_lon,
            "grouping": "false",
            "groupingDivisor": 15,
            "operator": "EnBW",
        }
        headers = {
            "Ocp-Apim-Subscription-Key": self.API_KEY,
            "Accept": "application/json",
            "Referer": "https://www.enbw.com/",
            "Origin": "https://www.enbw.com",
        }
        return JsonRequest(url=f"{self.API}?{urlencode(params)}", headers=headers, cb_kwargs={"bbox": bbox})

    def parse(self, response: Response, bbox: tuple[float, float, float, float], **kwargs: Any) -> Any:
        stations = response.json()
        from_lat, from_lon, to_lat, to_lon = bbox

        grouped = [s for s in stations if s["grouped"]]
        if grouped and (to_lat - from_lat) > self.MIN_SPAN and (to_lon - from_lon) > self.MIN_SPAN:
            mid_lat, mid_lon = (from_lat + to_lat) / 2, (from_lon + to_lon) / 2
            for sub_bbox in (
                (from_lat, from_lon, mid_lat, mid_lon),
                (from_lat, mid_lon, mid_lat, to_lon),
                (mid_lat, from_lon, to_lat, mid_lon),
                (mid_lat, mid_lon, to_lat, to_lon),
            ):
                yield self._cell_request(sub_bbox)
            return

        if grouped:
            self.logger.warning(f"Cell {bbox} still has {len(grouped)} grouped markers at minimum span; skipping")

        for station in stations:
            if station["grouped"] or not station.get("stationId"):
                continue
            yield self.parse_station(station)

    def parse_station(self, station: dict) -> Any:
        item = DictParser.parse(station)
        item["ref"] = str(station["stationId"])

        item.pop("addr_full", None)
        if address := station.get("shortAddress"):
            if m := ADDRESS_RE.match(address):
                item["street_address"] = m["street"]
                item["postcode"] = m["postcode"]
                item["city"] = m["city"]
                item["country"] = m["country"]
            else:
                item["addr_full"] = address

        item["extras"] = {"capacity": str(station["numberOfChargePoints"])}
        plug_types = station.get("plugTypes") or []
        if len(plug_types) == 1 and (socket := SOCKET_TYPES.get(plug_types[0])):
            item["extras"][f"socket:{socket}"] = str(station["numberOfChargePoints"])
            if power := station.get("maxPowerInKw"):
                item["extras"][f"socket:{socket}:output"] = f"{power} kW"

        if (wheelchair := station.get("handicappedAccessible")) is not None:
            apply_yes_no(Extras.WHEELCHAIR, item, wheelchair, False)

        apply_category(Categories.CHARGING_STATION, item)
        return item
