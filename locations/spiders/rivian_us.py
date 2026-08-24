import math
import struct
from typing import Any, AsyncIterator, Iterable, Iterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

TILE_URL = "https://api.rivianservices.com/map-chargers/tiles/chrg2/{}/{}/{}"
SEARCH_ZOOM = 7
BOUNDING_BOX = (-170.0, 18.0, -52.0, 72.0)
NETWORKS = ["Rivian Adventure Network", "Rivian Waypoints Network"]


def _read_varint(buf: memoryview, pos: int) -> tuple[int, int]:
    result = shift = 0
    while True:
        byte = buf[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, pos
        shift += 7


def _read_fields(buf: memoryview) -> Iterator[tuple[int, Any]]:
    """Yield the (field number, value) pairs of a protobuf message."""
    pos = 0
    while pos < len(buf):
        key, pos = _read_varint(buf, pos)
        field, wire_type = key >> 3, key & 0x07
        if wire_type == 0:
            value, pos = _read_varint(buf, pos)
        elif wire_type == 1:
            value, pos = buf[pos : pos + 8], pos + 8
        elif wire_type == 2:
            length, pos = _read_varint(buf, pos)
            value, pos = buf[pos : pos + length], pos + length
        elif wire_type == 5:
            value, pos = buf[pos : pos + 4], pos + 4
        else:
            raise ValueError(f"Unsupported protobuf wire type {wire_type}")
        yield field, value


def _read_tag_value(buf: memoryview) -> Any:
    for field, value in _read_fields(buf):
        if field == 1:
            return bytes(value).decode("utf-8")
        elif field == 2:
            return struct.unpack("<f", value)[0]
        elif field == 3:
            return struct.unpack("<d", value)[0]
        elif field in (4, 5):
            return value
        elif field == 6:
            return (value >> 1) ^ -(value & 1)
        elif field == 7:
            return bool(value)
    return None


def _read_packed_varints(buf: memoryview) -> list[int]:
    values, pos = [], 0
    while pos < len(buf):
        value, pos = _read_varint(buf, pos)
        values.append(value)
    return values


def tile_x(longitude: float, zoom: int) -> int:
    return int((longitude + 180.0) / 360.0 * 2**zoom)


def tile_y(latitude: float, zoom: int) -> int:
    return int((1.0 - math.asinh(math.tan(math.radians(latitude))) / math.pi) / 2.0 * 2**zoom)


def decode_vector_tile_points(raw: bytes, zoom: int, x: int, y: int) -> Iterator[tuple[str, dict, float, float]]:
    """
    Decode the point features of a Mapbox Vector Tile, yielding the layer name,
    the feature properties and the WGS84 coordinates of each one.

    https://github.com/mapbox/vector-tile-spec/blob/master/2.1/README.md
    """
    for field, layer in _read_fields(memoryview(raw)):
        if field != 3:
            continue
        extent, keys, values, features = 4096, [], [], []
        name = ""
        for layer_field, layer_value in _read_fields(layer):
            if layer_field == 1:
                name = bytes(layer_value).decode("utf-8")
            elif layer_field == 2:
                features.append(layer_value)
            elif layer_field == 3:
                keys.append(bytes(layer_value).decode("utf-8"))
            elif layer_field == 4:
                values.append(_read_tag_value(layer_value))
            elif layer_field == 5:
                extent = layer_value
        for feature in features:
            tags, geometry, geometry_type = [], [], 0
            for feature_field, feature_value in _read_fields(feature):
                if feature_field == 2:
                    tags = _read_packed_varints(feature_value)
                elif feature_field == 3:
                    geometry_type = feature_value
                elif feature_field == 4:
                    geometry = _read_packed_varints(feature_value)
            if geometry_type != 1 or len(geometry) < 3 or geometry[0] & 0x07 != 1:
                continue
            offset_x = (geometry[1] >> 1) ^ -(geometry[1] & 1)
            offset_y = (geometry[2] >> 1) ^ -(geometry[2] & 1)
            tiles = 2**zoom
            longitude = (x + offset_x / extent) / tiles * 360.0 - 180.0
            latitude = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + offset_y / extent) / tiles))))
            yield name, {keys[k]: values[v] for k, v in zip(tags[0::2], tags[1::2])}, latitude, longitude


class RivianUSSpider(Spider):
    """
    Rivian Adventure Network DC fast chargers and Rivian Waypoints destination
    chargers, from the vector tiles behind https://rivian.com/experience/charging
    """

    name = "rivian_us"
    custom_settings = {"CONCURRENT_REQUESTS_PER_DOMAIN": 1}
    item_attributes = {"operator": "Rivian", "operator_wikidata": "Q7338847"}
    allowed_domains = ["api.rivianservices.com"]
    seen_refs: set[str] = set()

    async def start(self) -> AsyncIterator[Request]:
        west, south, east, north = BOUNDING_BOX
        for x in range(tile_x(west, SEARCH_ZOOM), tile_x(east, SEARCH_ZOOM) + 1):
            for y in range(tile_y(north, SEARCH_ZOOM), tile_y(south, SEARCH_ZOOM) + 1):
                yield Request(
                    url=TILE_URL.format(SEARCH_ZOOM, x, y),
                    callback=self.parse_tile,
                    cb_kwargs={"x": x, "y": y},
                )

    def parse_tile(self, response: Response, x: int, y: int, **kwargs: Any) -> Iterable[Feature]:
        if not response.body:
            return

        for layer, properties, latitude, longitude in decode_vector_tile_points(response.body, SEARCH_ZOOM, x, y):
            if layer != "Charger" or properties.get("network") not in NETWORKS:
                continue
            if properties["id"] in self.seen_refs:
                continue
            self.seen_refs.add(properties["id"])

            item = Feature()
            item["ref"] = properties["id"]
            item["branch"] = properties.get("name")
            item["lat"] = latitude
            item["lon"] = longitude
            item["country"] = "US"
            self.parse_address(item, properties["address"])

            item["extras"]["brand"] = properties["network"]
            item["extras"]["capacity"] = str(properties["count"])
            item["extras"]["motorcar"] = "yes"
            item["extras"]["charging_station:output"] = "{} kW".format(properties["maxkw"])
            item["extras"]["access"] = "customers" if properties.get("rivianonly") else "yes"

            apply_category(Categories.CHARGING_STATION, item)

            yield item

    def parse_address(self, item: Feature, address: str) -> None:
        """Split a "street, city, state postcode, country" formatted address."""
        parts = [part.strip() for part in address.split(",") if part.strip()]
        if len(parts) < 4:
            item["addr_full"] = address
            return
        state, _, postcode = parts[-2].partition(" ")
        item["street_address"] = ", ".join(parts[:-3])
        item["city"] = parts[-3]
        item["state"] = state
        item["postcode"] = postcode
