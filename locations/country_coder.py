"""
Resolve the location identifiers used in NSI ``locationSet``s to ISO 3166-1 alpha-2 country codes.

NSI resolves locationSets with location-conflation, which in turn uses country-coder
(https://github.com/rapideditor/country-coder) to turn identifiers — ISO codes, UN M49 codes, Wikidata
IDs, names and aliases such as "conus" — into geometry. Our consumers only match on country codes, so at
vendoring time we collapse every identifier to the set of alpha-2 codes it covers, using country-coder's
own data. See https://github.com/osmlab/name-suggestion-index/wiki/Item-Property-Reference#locationset
"""

import logging
import re
from collections import defaultdict

import requests
import reverse_geocoder
from pyproj import Geod
from shapely.geometry import shape

logger = logging.getLogger(__name__)

BORDERS_URL = "https://cdn.jsdelivr.net/npm/@rapideditor/country-coder@5/src/data/borders.json"
WORLD_M49_CODE = "001"
DEFAULT_CIRCLE_RADIUS_KM = 25

# ISO 3166-1 exceptional reservations -> the officially assigned code that geocoders emit.
# Clipperton (CP) is uninhabited and would only drag FR into the Americas.
EXCEPTIONAL_RESERVATIONS = {
    "AC": "SH",
    "CP": None,
    "CQ": "GG",
    "DG": "IO",
    "EA": "ES",
    "FX": "FR",
    "IC": "ES",
    "TA": "SH",
}

# Territories that country-coder files under a country but that NSI and our pipelines treat as separate
# markets: NSI lists separate HK/MO entries for brands that also have a CN one.
NOT_PART_OF_COUNTRY = {"HK", "MO"}

# Ported from country-coder's canonicalID(): drop and/the/of/el/la/de and punctuation, then uppercase.
M49_REGION_LEVELS = ("region", "subregion", "intermediateRegion")

_ID_FILTER_RE = re.compile(r"\b(and|the|of|el|la|de)\b|[-_ .,'()&\[\]/]", re.IGNORECASE)
_ISO2_RE = re.compile(r"^[a-z]{2}$", re.IGNORECASE)
_SUBDIVISION_RE = re.compile(r"^[a-z]{2}-[a-z0-9]+$", re.IGNORECASE)


def canonical_id(identifier: str) -> str:
    if identifier.startswith("."):
        return identifier.upper()
    if re.fullmatch(r"and|the|of|el|la|de", identifier, re.IGNORECASE):
        return identifier.upper()
    return _ID_FILTER_RE.sub("", identifier).upper()


class CountryCoder:
    """
    Index of country-coder's borders.json, answering "which ISO2 codes does this identifier cover?".
    Ported only as far as ID lookup and group membership; no geometry.
    """

    _identifier_props = ("iso1A2", "iso1A3", "m49", "wikidata", "emojiFlag", "ccTLD", "nameEn")

    def __init__(self, borders: dict):
        self._by_code: dict[str, dict] = {}
        self._members: dict[str, list[dict]] = defaultdict(list)
        features = []
        for f in borders["features"]:
            if f["properties"].get("level") in ("union", "unitedNations", "world"):
                continue
            f["properties"]["geometry"] = f.get("geometry")
            features.append(f["properties"])
        for props in features:
            props.setdefault("m49", props.get("iso1N3"))
            props["id"] = props.get("iso1A2") or props.get("m49") or props.get("wikidata") or props["nameEn"]
            for prop in self._identifier_props:
                if props.get(prop):
                    self._by_code[canonical_id(props[prop])] = props
            for alias in props.get("aliases", []):
                self._by_code[canonical_id(alias)] = props
        self._official_iso2 = {
            p["iso1A2"] for p in features if p.get("iso1A2") and p["iso1A2"] not in EXCEPTIONAL_RESERVATIONS
        }
        for props in features:
            for group in props.get("groups", []):
                self._members[canonical_id(group)].append(props)
            # As in country-coder, a country is the union of every feature that names it as its country, so
            # "fr" covers Guadeloupe and "us" covers Puerto Rico.
            if props.get("geometry") and props.get("country") and props.get("iso1A2") not in NOT_PART_OF_COUNTRY:
                self._members[canonical_id(props["country"])].append(props)

    @classmethod
    def from_url(cls, url: str = BORDERS_URL) -> "CountryCoder":
        return cls(requests.get(url).json())

    def feature(self, identifier: str) -> dict | None:
        return self._by_code.get(canonical_id(identifier))

    def resolve(self, identifier: str) -> set[str] | None:
        """
        ISO2 codes (lowercase) covered by an identifier, or None if country-coder doesn't know it.

        A country resolves to itself plus its ISO-coded territories (fr -> fr, gp, mq, ...); a territory
        resolves to itself only, so "fx" stays Metropolitan France. A named sub-country place (England, Crimea,
        Northern Cyprus) resolves to whatever our reverse geocoder calls it, so the code agrees with the
        country our pipelines put on POIs there rather than with country-coder's political model. M49
        regions resolve by membership; other groups (US States, the Cyprus landform) by membership with
        the geocoder as fallback.
        """
        props = self.feature(identifier)
        if props is None:
            return None
        if props.get("iso1A2"):
            code = self._country_code(props)
            codes = {code} if code else set()
            return codes | {
                c for member in self._members[canonical_id(props["iso1A2"])] if (c := self._country_code(member))
            }
        if props.get("geometry"):
            return countries_in_geometry(props["geometry"])
        members = self._members[canonical_id(props["id"])]
        if not members:
            code = self._country_code(props)
            return {code} if code else set()
        geocode_fallback = props.get("level") not in M49_REGION_LEVELS
        codes = set()
        for member in members:
            if code := self._country_code(member):
                codes.add(code)
            elif geocode_fallback and member.get("geometry"):
                codes |= countries_in_geometry(member["geometry"])
        return codes

    def _country_code(self, props: dict) -> str | None:
        if code := props.get("iso1A2"):
            code = EXCEPTIONAL_RESERVATIONS.get(code, code)
            return code.lower() if code else None
        # Sub-features without their own code roll up to the nearest ISO-coded group (Bonaire -> BQ,
        # Svalbard -> SJ), else to their country (England -> GB). Subterritories don't roll up to the
        # country, so Ceuta doesn't put Spain in Africa.
        parent = next((g for g in props.get("groups", []) if g in self._official_iso2), None)
        if parent:
            return parent.lower()
        if props.get("level") == "subterritory":
            return None
        return props["country"].lower() if props.get("country") else None


def countries_in_geometry(geometry: dict) -> set[str]:
    """Countries our reverse geocoder assigns to a (Multi)Polygon, sampled at one interior point per polygon."""
    geom = shape(geometry)
    polygons = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    points = [(p.representative_point().y, p.representative_point().x) for p in polygons]
    return {result["cc"].lower() for result in reverse_geocoder.search(points, mode=1, verbose=False)}


def countries_in_circle(lon: float, lat: float, radius_km: float) -> set[str]:
    """Countries touched by a circular locationSet, sampled at the centre and eight compass points on the edge."""
    geod = Geod(ellps="WGS84")
    coords = [(lat, lon)]
    for bearing in range(0, 360, 45):
        new_lon, new_lat, _ = geod.fwd(lon, lat, bearing, radius_km * 1000)
        coords.append((new_lat, new_lon))
    return {result["cc"].lower() for result in reverse_geocoder.search(coords, mode=1, verbose=False)}


def resolve_location_set(location_set: dict, coder: CountryCoder, context: str = "") -> dict:
    """
    Rewrite an NSI locationSet so it only contains what our consumers match on: lowercase ISO2 codes,
    "cc-xxx" subdivision codes, "*.geojson" custom features and the world code "001".

    Everything else — UN M49 regions, ISO3 codes, Wikidata IDs, country-coder aliases and names — is expanded
    to country codes. Circles are expanded when included and dropped when excluded, as we would rather keep a
    brand in a whole country than lose it over a small area. Unknown identifiers are kept and logged as errors.
    """
    resolved = {}
    for side in ("include", "exclude"):
        codes = set()
        for location in location_set.get(side, []):
            if isinstance(location, list):
                if side == "include":
                    radius = location[2] if len(location) == 3 else DEFAULT_CIRCLE_RADIUS_KM
                    codes |= countries_in_circle(location[0], location[1], radius)
                continue
            if location == WORLD_M49_CODE or location.endswith(".geojson") or _SUBDIVISION_RE.match(location):
                codes.add(location)
                continue
            countries = coder.resolve(location)
            if countries is None:
                if not _ISO2_RE.match(location):
                    logger.error(f"Unknown locationSet identifier {location!r} in {context}; kept as is")
                codes.add(location)
                continue
            codes |= countries
        if codes or side in location_set:
            resolved[side] = sorted(codes)
    return resolved
