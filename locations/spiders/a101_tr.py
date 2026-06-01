from base64 import b64encode
from json import dumps
from math import sqrt
from typing import AsyncIterator

from pygeohash import encode
from pyproj import Geod
from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import point_locations, vincenty_distance

WGS84 = Geod(ellps="WGS84")
SQRT2 = sqrt(2)  # a square cell's circumradius is its half-width × √2


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    _, _, metres = WGS84.inv(lon1, lat1, lon2, lat2)
    return metres / 1000


class A101TRSpider(Spider):
    name = "a101_tr"
    item_attributes = {"brand": "A101", "brand_wikidata": "Q6034496"}
    requires_proxy = True
    custom_settings = {
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 2,
        "ROBOTSTXT_OBEY": False,
    }

    # The API returns the N nearest stores to a geohash point, so a single
    # query reveals every store within a disc whose radius is the distance to
    # the farthest (Nth) returned store. A cell is fully covered once that
    # cleared radius reaches its corners; only cells that hit the result cap
    # *and* are not yet fully cleared need subdividing. Start from a coarse grid
    # and recurse, with a floor to bound depth in pathologically dense spots.
    API_RESULT_CAP = 20
    INITIAL_HALF_KM = 120.0
    MIN_CELL_HALF_KM = 0.1
    # The completeness guarantee is strict: every store *closer* than the farthest
    # returned one is included, but a store exactly at that distance may be dropped
    # when it ties with the result-cap boundary. Shrink the cleared radius by this
    # margin so the disc stays strictly inside the guaranteed-complete region (also
    # absorbs metre-level noise between the API distance and our recomputed one).
    CLEARED_MARGIN_KM = 0.01
    # How finely a candidate cell may be split when testing whether the union of
    # already-cleared discs covers it. Each level quarters the cell, so deeper
    # values catch cells covered piecewise by several discs at more compute cost.
    COVERAGE_DEPTH = 5
    # Compass bearings to the four quadrant centres (NE, SE, SW, NW).
    QUADRANT_BEARINGS = (45, 135, 225, 315)
    URL_TEMPLATE = "https://rio.a101.com.tr/dbmk89vnr/CALL/StoreContentManager/nearestStores/default?__culture=tr-TR&__platform=web&data={}&__isbase64=true"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_refs: set[str] = set()
        # Every query reveals all stores within (lat, lon, cleared_km); used to
        # skip child cells that earlier queries have already fully covered.
        self.cleared_discs: list[tuple[float, float, float]] = []

    async def start(self) -> AsyncIterator[Request]:
        for lat, lon in point_locations("eu_centroids_120km_radius_country.csv", "TR"):
            yield self._cell_request(lat, lon, self.INITIAL_HALF_KM)

    def _cell_request(self, lat: float, lon: float, half_km: float) -> Request:
        data = {"geoHash": encode(lat, lon, precision=9)}
        data = b64encode(dumps(data).encode("utf-8")).decode("utf-8")
        return Request(
            url=self.URL_TEMPLATE.format(data),
            callback=self.parse,
            cb_kwargs={"lat": lat, "lon": lon, "half_km": half_km},
        )

    def parse(self, response, lat: float, lon: float, half_km: float):
        stores = response.json().get("stores", [])
        for poi in stores:
            item = DictParser.parse(poi)
            if item.get("ref") in self.seen_refs:
                continue
            self.seen_refs.add(item["ref"])
            item["street_address"] = item.pop("addr_full")
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item

        if not stores:
            return

        # The farthest returned store marks the radius within which the API has
        # revealed every store; record it (less a safety margin) so later cells
        # covered by it can be skipped.
        farthest_km = max(poi.get("distance", 0) for poi in stores) / 1000
        cleared_km = max(0.0, farthest_km - self.CLEARED_MARGIN_KM)
        self.cleared_discs.append((lat, lon, cleared_km))

        # Stop subdividing if every nearby store was already returned (below the
        # cap), the depth floor is reached, or the cleared disc already reaches
        # the cell's corners — in all three cases nothing new is left to find.
        if len(stores) < self.API_RESULT_CAP or half_km <= self.MIN_CELL_HALF_KM:
            return
        if cleared_km >= half_km * SQRT2:
            return

        for child_lat, child_lon, child_half in self._quadrants(lat, lon, half_km):
            if self.cell_is_covered(child_lat, child_lon, child_half):
                self.crawler.stats.inc_value("a101/cells_skipped_covered")
                self.logger.debug("skip covered cell %.4f,%.4f half=%.2fkm", child_lat, child_lon, child_half)
            else:
                yield self._cell_request(child_lat, child_lon, child_half)

    def _quadrants(self, lat: float, lon: float, half_km: float):
        """Yield (lat, lon, half_km) of the four quadrant sub-cells that tile
        this cell. Each child centre is half_km/2 away on each axis, i.e.
        half_km/√2 diagonally along a corner bearing."""
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
        """True if the cell lies entirely within the union of the given discs,
        so re-querying it cannot surface any unseen store: either a single disc
        contains it, or its quadrants are each (recursively) covered."""
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
