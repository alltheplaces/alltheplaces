"""
AllThePlaces spider — The Church of Jesus Christ of Latter-day Saints
======================================================================
Source:  maps.churchofjesuschrist.org/api/maps-proxy/v2/
Layer:   MEETINGHOUSE
Method:  Option B — Church Maps v2 API (anonymous, no Yext dependency)

ATP output: GeoJSON Feature with standard OSM-compatible fields.
Google Place ID is preserved in extras["ref:google"] where returned by the API.

Place this file at:
  locations/spiders/church_of_jesus_christ_latter_day_saints.py

No additional dependencies beyond those already in ATP's requirements.txt.
The spider uses Scrapy's native Request mechanism rather than the
standalone requests library used by moroni-tools/scraper.py.

Worldwide coverage is achieved through geographic bounding-box subdivision.
Starting zoom=2 (continental tiles), recursing to zoom=12 for dense areas.

Cluster threshold: when the API reports more than CLUSTER_THRESHOLD items
in a tile, the tile is subdivided before individual markers are resolved.
"""

from __future__ import annotations

from typing import Any, Generator

import scrapy

from locations.dict_parser import DictParser
from locations.items import Feature

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

API_BASE = "https://maps.churchofjesuschrist.org/api/maps-proxy/v2"
CLUSTERS_URL = f"{API_BASE}/locations/clusters"
IDENTIFY_URL = f"{API_BASE}/locations/identify"
LOCATIONS_URL = f"{API_BASE}/locations"

WORLD_EXTENT = "-180,-90,180,90"
MIN_ZOOM = 2
MAX_ZOOM = 12
CLUSTER_THRESHOLD = 50  # subdivide if cluster count exceeds this

# 2026-11-12: API now requires Referer header; bare requests return HTTP 401.
HEADERS = {
    "Accept": "application/json",
    "Referer": "https://maps.churchofjesuschrist.org/",
    "Origin": "https://maps.churchofjesuschrist.org",
    "X-Maps-Client": "alltheplaces-spider",
}

# Manitoba regression fixtures (Moroni build spec §3.9) — spot-check only
MANITBA_SAMPLE_ID = "5126835-01-01"


# ---------------------------------------------------------------------------
# Spider
# ---------------------------------------------------------------------------


class ChurchOfJesusChristLatterDaySaintsSpider(scrapy.Spider):
    name = "church_of_jesus_christ_latter_day_saints"
    item_attributes = {
        "brand": "The Church of Jesus Christ of Latter-day Saints",
        "brand_wikidata": "Q42504",
        "nsi_id": "thechurchofjesuschristoflatterdaysaints-155571",
    }
    # ATP coding guidelines require this attribute
    allowed_domains = ["maps.churchofjesuschrist.org"]

    def start_requests(self) -> Generator[scrapy.Request, None, None]:
        yield self._cluster_request(WORLD_EXTENT, zoom=MIN_ZOOM)

    # ------------------------------------------------------------------
    # Cluster discovery
    # ------------------------------------------------------------------

    def _cluster_request(self, extent: str, zoom: int) -> scrapy.Request:
        return scrapy.Request(
            url=CLUSTERS_URL,
            method="GET",
            headers=HEADERS,
            cb_kwargs={"extent": extent, "zoom": zoom},
            callback=self.parse_clusters,
            meta={"extent": extent, "zoom": zoom},
        )

    def parse_clusters(
        self, response: scrapy.http.Response, extent: str, zoom: int
    ) -> Generator[scrapy.Request | Feature, None, None]:
        data = response.json()
        items = data if isinstance(data, list) else data.get("results", data.get("items", []))
        if not items:
            return

        for item in items:
            count = item.get("count", 0)
            sub_items = item.get("items") or []
            item_type = str(item.get("type", "")).upper()
            is_cluster = count > 1 or (not sub_items and item_type not in ("MARKER", "LOCATION"))

            coords = item.get("coordinates") or (item.get("geometry", {}).get("coordinates"))
            if isinstance(coords, list) and len(coords) >= 2:
                item_lng, item_lat = float(coords[0]), float(coords[1])
            else:
                item_lng, item_lat = None, None

            if is_cluster and zoom < MAX_ZOOM:
                # Recurse: use the cluster's own extent if provided
                sub_extent = item.get("extent")
                if sub_extent and isinstance(sub_extent, dict):
                    sub_extent = (
                        f"{sub_extent.get('min_lng', sub_extent.get('west', -180))},"
                        f"{sub_extent.get('min_lat', sub_extent.get('south', -90))},"
                        f"{sub_extent.get('max_lng', sub_extent.get('east', 180))},"
                        f"{sub_extent.get('max_lat', sub_extent.get('north', 90))}"
                    )
                elif sub_extent and isinstance(sub_extent, str):
                    pass  # already a string
                else:
                    sub_extent = None

                if sub_extent:
                    yield self._cluster_request(sub_extent, zoom + 2)
                else:
                    for quad in self._subdivide(extent):
                        yield self._cluster_request(quad, zoom + 2)

            elif item_lng is not None and item_lat is not None:
                # Individual marker — resolve via /identify
                facility_id = item.get("facilityId") or item.get("id") or item.get("facility_id_identifier")
                yield scrapy.Request(
                    url=IDENTIFY_URL,
                    method="GET",
                    headers=HEADERS,
                    cb_kwargs={"facility_id": facility_id},
                    callback=self.parse_identify,
                    meta={
                        "lng": item_lng,
                        "lat": item_lat,
                        "facility_id": facility_id,
                    },
                )

    # ------------------------------------------------------------------
    # Location detail
    # ------------------------------------------------------------------

    def parse_identify(self, response: scrapy.http.Response, facility_id: str | None) -> Generator[Feature, None, None]:
        data = response.json()
        # /identify returns list of nearest matches
        records = data if isinstance(data, list) else [data]
        for record in records:
            item = self._map_record(record)
            if item:
                # Only yield if facility_id matches (or we have no id to check)
                if facility_id and item.get("ref") and item["ref"] != facility_id:
                    continue
                yield item

    def _map_record(self, record: dict) -> Feature | None:
        """Map a /locations/identify response record to an ATP Feature."""
        if not record:
            return None

        item = Feature()

        # DictParser handles common field-name variations automatically
        DictParser.parse(item, record)

        # Explicit overrides for LDS-specific field names
        facility_id = record.get("facilityId") or record.get("facility_id_identifier") or record.get("id")
        item["ref"] = facility_id or item.get("ref", "")
        item["name"] = (
            record.get("name")
            or record.get("displayName")
            or record.get("meetinghouse_name")
            or "The Church of Jesus Christ of Latter-day Saints"
        )

        # Coordinates — try multiple nesting patterns
        lat = record.get("latitude") or record.get("lat")
        lng = record.get("longitude") or record.get("lng") or record.get("lon")
        if not lat or not lng:
            coords = record.get("geometry", {}).get("coordinates", [])
            if len(coords) >= 2:
                lng, lat = coords[0], coords[1]
        if lat and lng:
            item["lat"] = float(lat)
            item["lon"] = float(lng)
        else:
            return None  # coordinates required

        # Address
        item["addr_full"] = record.get("formattedAddress") or record.get("formatted_address") or ""
        item["street"] = record.get("streetAddress") or record.get("street_1") or ""
        item["city"] = record.get("city", "")
        item["state"] = record.get("state") or record.get("stateCode") or record.get("state_code") or ""
        item["postcode"] = record.get("postalCode") or record.get("zip") or record.get("postal_code") or ""
        item["country"] = record.get("country") or record.get("countryCode") or record.get("country_code_2") or ""
        item["county"] = record.get("county", "")

        # Phone / website
        item["phone"] = record.get("phone", "")
        item["website"] = record.get("website") or "https://www.churchofjesuschrist.org/"

        # Google Place ID — preserved for Moroni category monitoring
        google_place_id = record.get("googlePlaceId") or record.get("google_place_id")
        if google_place_id:
            item.setdefault("extras", {})["ref:google"] = f"place_id:{google_place_id}"

        # LDS-specific identifiers preserved as extras for Moroni reconciliation
        extras: dict[str, Any] = item.get("extras") or {}
        if record.get("structureId") or record.get("structure_id"):
            extras["ref:lds:structure_id"] = record.get("structureId") or record.get("structure_id")
        if record.get("propertyId") or record.get("property_id"):
            extras["ref:lds:property_id"] = record.get("propertyId") or record.get("property_id")
        item["extras"] = extras

        # Brand / category
        item["brand"] = "The Church of Jesus Christ of Latter-day Saints"
        item["brand_wikidata"] = "Q42504"
        item["nsi_id"] = "thechurchofjesuschristoflatterdaysaints-155571"

        return item

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _subdivide(extent: str) -> list[str]:
        """Split bounding box into four quadrant tiles."""
        w, s, e, n = (float(v) for v in extent.split(","))
        mx, my = (w + e) / 2, (s + n) / 2
        return [
            f"{w},{s},{mx},{my}",
            f"{mx},{s},{e},{my}",
            f"{w},{my},{mx},{n}",
            f"{mx},{my},{e},{n}",
        ]
