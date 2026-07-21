from math import sqrt
from typing import Any, AsyncIterator

from pyproj import Geod
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import point_locations, vincenty_distance

WGS84 = Geod(ellps="WGS84")
SQRT2 = sqrt(2)  # a square cell's circumradius is its half-width × √2


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    _, _, metres = WGS84.inv(lon1, lat1, lon2, lat2)
    return metres / 1000


class GaliciaARSpider(Spider):
    name = "galicia_ar"
    item_attributes = {"brand": "Galicia", "brand_wikidata": "Q5717952"}

    # The locator only exposes a "nearest branches to a coordinate" endpoint (no bulk/all mode; it
    # ignores any radius/count parameter and always returns the 10 nearest), so the country is covered
    # with an adaptive quadtree — the same approach as a101_tr. A query reveals every branch within a
    # disc whose radius is the distance to the farthest returned branch; a cell is fully covered once
    # that cleared radius reaches its corners, so only cells that hit the result cap and are not yet
    # cleared are subdivided (dense Buenos Aires recurses deep, empty regions stay coarse).
    API = "https://www.galicia.ar/services/sucursales"
    API_RESULT_CAP = 10
    INITIAL_HALF_KM = 158.0
    MIN_CELL_HALF_KM = 0.1
    CLEARED_MARGIN_KM = 0.01  # keep the cleared disc strictly inside the guaranteed-complete region
    COVERAGE_DEPTH = 5  # how finely a child cell is tested against the union of cleared discs
    QUADRANT_BEARINGS = (45, 135, 225, 315)  # NE, SE, SW, NW

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.cleared_discs: list[tuple[float, float, float]] = []

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in point_locations("iseadgg/ar_centroids_iseadgg_158km_radius.csv"):
            yield self._cell_request(lat, lon, self.INITIAL_HALF_KM)

    def _cell_request(self, lat: float, lon: float, half_km: float) -> JsonRequest:
        return JsonRequest(
            url=self.API,
            data={"latitud": lat, "longitud": lon},
            headers={"Referer": "https://www.galicia.ar/personas/sucursales"},  # required; 403 without it
            cb_kwargs={"lat": lat, "lon": lon, "half_km": half_km},
        )

    def parse(self, response: Response, lat: float, lon: float, half_km: float) -> Any:
        branches = response.json().get("listaPuntos", [])
        for poi in branches:
            # "address" is free-form (street + number + a locality that is a city in the interior but a
            # neighbourhood in Buenos Aires, with no delimiter), so DictParser's addr_full is kept as-is
            # rather than split or relabelled as street_address.
            item = DictParser.parse(poi)  # maps lat/long and "address" (-> addr_full)
            item.pop("name", None)  # NSI provides the brand name
            code, _, label = poi["name"].partition(" - ")  # e.g. "SU 680 - CASA CENTRAL"
            item["ref"] = code.removeprefix("SU").strip()
            item["branch"] = label or None
            apply_category(Categories.BANK, item)
            yield item

        if not branches:
            return

        # Distance to the farthest returned branch = radius within which every branch is now known.
        farthest_km = max(distance_km(lat, lon, float(poi["lat"]), float(poi["long"])) for poi in branches)
        cleared_km = max(0.0, farthest_km - self.CLEARED_MARGIN_KM)
        self.cleared_discs.append((lat, lon, cleared_km))

        # Nothing new to find if the whole cell was returned below the cap, the depth floor is hit, or
        # the cleared disc already reaches the cell's corners.
        if len(branches) < self.API_RESULT_CAP or half_km <= self.MIN_CELL_HALF_KM:
            return
        if cleared_km >= half_km * SQRT2:
            return

        for child_lat, child_lon, child_half in self._quadrants(lat, lon, half_km):
            if not self.cell_is_covered(child_lat, child_lon, child_half):
                yield self._cell_request(child_lat, child_lon, child_half)

    def _quadrants(self, lat: float, lon: float, half_km: float):
        child_half = half_km / 2
        diagonal = half_km / SQRT2
        for bearing in self.QUADRANT_BEARINGS:
            child_lat, child_lon = vincenty_distance(lat, lon, diagonal, bearing)
            yield child_lat, child_lon, child_half

    def cell_is_covered(self, lat: float, lon: float, half_km: float) -> bool:
        """True if the union of already-cleared discs fully covers this cell."""
        circumradius = half_km * SQRT2
        nearby = [d for d in self.cleared_discs if distance_km(d[0], d[1], lat, lon) <= circumradius + d[2]]
        return self._covered(lat, lon, half_km, nearby, self.COVERAGE_DEPTH)

    def _covered(self, lat: float, lon: float, half_km: float, discs: list, depth: int) -> bool:
        cell_radius_km = half_km * SQRT2
        if any(
            r >= cell_radius_km and distance_km(clat, clon, lat, lon) + cell_radius_km <= r for clat, clon, r in discs
        ):
            return True
        if depth <= 0:
            return False
        return all(
            self._covered(clat, clon, ch, discs, depth - 1) for clat, clon, ch in self._quadrants(lat, lon, half_km)
        )
