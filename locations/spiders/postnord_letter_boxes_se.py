import gzip
import math
import struct
from datetime import date, datetime
from typing import Any, AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS
from locations.items import Feature


def _varint(buf: memoryview, i: int) -> tuple[int, int]:
    result = shift = 0
    while True:
        b = buf[i]
        i += 1
        result |= (b & 0x7F) << shift
        shift += 7
        if not b & 0x80:
            return result, i


def _fields(buf: memoryview) -> Iterable[tuple[int, Any]]:
    """Iterate over the (field number, value) pairs of a protobuf message."""
    i = 0
    while i < len(buf):
        key, i = _varint(buf, i)
        field, wire_type = key >> 3, key & 7
        if wire_type == 0:
            value, i = _varint(buf, i)
        elif wire_type == 2:
            length, i = _varint(buf, i)
            value = buf[i : i + length]
            i += length
        elif wire_type == 1:
            value = buf[i : i + 8]
            i += 8
        elif wire_type == 5:
            value = buf[i : i + 4]
            i += 4
        else:
            raise ValueError(f"Unsupported protobuf wire type {wire_type}")
        yield field, value


def _packed(buf: memoryview) -> list[int]:
    values, i = [], 0
    while i < len(buf):
        value, i = _varint(buf, i)
        values.append(value)
    return values


def _zigzag(n: int) -> int:
    return (n >> 1) ^ -(n & 1)


def _tile_value(buf: memoryview) -> Any:
    for field, value in _fields(buf):
        if field == 1:
            return bytes(value).decode()
        if field == 2:
            return struct.unpack("<f", value)[0]
        if field == 3:
            return struct.unpack("<d", value)[0]
        if field in (4, 5):
            return value - (1 << 64) if value >= 1 << 63 else value
        if field == 6:
            return _zigzag(value)
        if field == 7:
            return bool(value)
    return None


def decode_point_tile(data: bytes) -> Iterable[tuple[int, dict, list[tuple[int, int]]]]:
    """Minimal Mapbox Vector Tile decoder yielding (extent, properties, points) for every feature."""
    for field, layer in _fields(memoryview(data)):
        if field != 3:
            continue
        keys, values, features, extent = [], [], [], 4096
        for layer_field, value in _fields(layer):
            if layer_field == 2:
                features.append(value)
            elif layer_field == 3:
                keys.append(bytes(value).decode())
            elif layer_field == 4:
                values.append(_tile_value(value))
            elif layer_field == 5:
                extent = value
        for feature in features:
            tags, geometry = [], []
            for feature_field, value in _fields(feature):
                if feature_field == 2:
                    tags = _packed(value)
                elif feature_field == 4:
                    geometry = _packed(value)
            properties = {keys[tags[k]]: values[tags[k + 1]] for k in range(0, len(tags), 2)}
            points, i, x, y = [], 0, 0, 0
            while i < len(geometry):
                command, count = geometry[i] & 7, geometry[i] >> 3
                i += 1
                if command in (1, 2):
                    for _ in range(count):
                        x += _zigzag(geometry[i])
                        y += _zigzag(geometry[i + 1])
                        i += 2
                        points.append((x, y))
            yield extent, properties, points


def tile_to_lat_lon(z: int, x: float, y: float) -> tuple[float, float]:
    n = 2**z
    lon = x / n * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lat, lon


class PostnordLetterBoxesSESpider(Spider):
    """
    Letter boxes from PostNord's "Hitta brevlåda" map, read from the vector tiles behind it.

    Low zoom tiles hold every box but with coarse coordinates, so an overview pass at OVERVIEW_ZOOM
    lists the boxes and picks the DETAIL_ZOOM tiles (about 1 m precision in Sweden) to fetch.
    """

    name = "postnord_letter_boxes_se"
    item_attributes = {"operator": "PostNord", "operator_wikidata": "Q3181430"}
    allowed_domains = ["tiles-prod.pgm.postnord.com"]

    TILE_URL = "https://tiles-prod.pgm.postnord.com/pgtile/mbs.mailbox_empty_time_view/{z}/{x}/{y}.pbf"
    OVERVIEW_ZOOM = 6
    DETAIL_ZOOM = 12
    # Overview tiles covering Sweden (lon 10.9..24.2, lat 55.3..69.1).
    OVERVIEW_X = range(33, 37)
    OVERVIEW_Y = range(14, 21)

    expected: set[int]
    seen: set[int]

    async def start(self) -> AsyncIterator[Request]:
        self.expected, self.seen = set(), set()
        for x in self.OVERVIEW_X:
            for y in self.OVERVIEW_Y:
                yield Request(
                    self.TILE_URL.format(z=self.OVERVIEW_ZOOM, x=x, y=y),
                    callback=self.parse_overview,
                    cb_kwargs={"x": x, "y": y},
                )

    @staticmethod
    def read_tile(response: Response) -> Iterable[tuple[int, dict, list[tuple[int, int]]]]:
        body = response.body
        if body[:2] == b"\x1f\x8b":
            body = gzip.decompress(body)
        return decode_point_tile(body)

    def parse_overview(self, response: Response, x: int, y: int) -> Iterable[Request]:
        scale = 2 ** (self.DETAIL_ZOOM - self.OVERVIEW_ZOOM)
        detail_tiles = set()
        for extent, properties, points in self.read_tile(response):
            if not points:
                continue
            u, v = points[0]
            # Features in the tile buffer belong to (and are listed by) the neighbouring tile.
            if not (0 <= u < extent and 0 <= v < extent):
                continue
            self.expected.add(properties["id"])
            # Overview coordinates are rounded to a pixel; allow for that at tile boundaries.
            margin = 1 / extent * scale
            gx, gy = (x + u / extent) * scale, (y + v / extent) * scale
            for tx in {math.floor(gx - margin), math.floor(gx + margin)}:
                for ty in {math.floor(gy - margin), math.floor(gy + margin)}:
                    detail_tiles.add((tx, ty))
        for tx, ty in sorted(detail_tiles):
            # Requests for the same tile from neighbouring overview tiles are dropped by the dupe filter.
            yield Request(
                self.TILE_URL.format(z=self.DETAIL_ZOOM, x=tx, y=ty),
                callback=self.parse_detail,
                cb_kwargs={"x": tx, "y": ty},
            )

    def parse_detail(self, response: Response, x: int, y: int) -> Iterable[Feature]:
        for extent, properties, points in self.read_tile(response):
            if not points:
                continue
            # Boxes in a tile's buffer are repeated by its neighbours; DuplicatesPipeline drops the repeats.
            # self.seen is only for the missing-box stats in closed().
            self.seen.add(properties["id"])
            u, v = points[0]
            lat, lon = tile_to_lat_lon(self.DETAIL_ZOOM, x + u / extent, y + v / extent)
            yield self.parse_box(properties, lat, lon)

    def parse_box(self, box: dict, lat: float, lon: float) -> Feature:
        item = Feature()
        item["ref"] = str(box["id"])
        item["lat"] = round(lat, 6)
        item["lon"] = round(lon, 6)
        item["street_address"] = ", ".join(filter(None, [box.get("address"), box.get("address2")]))
        item["postcode"] = box.get("postalcode")
        item["city"] = box.get("postalcity")
        apply_category(Categories.POST_BOX, item)
        if collection_times := self.parse_collection_times(box):
            item["extras"]["collection_times"] = collection_times
        return item

    @staticmethod
    def format_time(value: str | None) -> str | None:
        if value and len(value) == 4 and value.isdigit():
            return f"{value[:2]}:{value[2:]}"
        return None

    @staticmethod
    def emptied_dates(box: dict) -> list[date]:
        # A Postgres array literal of upcoming collections: {"2026-10-06 09:00:00","2026-10-08 09:00:00"}
        dates = []
        for value in (box.get("emptied_at") or "").strip("{}").split(","):
            value = value.strip().strip('"')
            try:
                dates.append(datetime.fromisoformat(value).date())
            except ValueError:
                continue
        return sorted(dates)

    def parse_collection_times(self, box: dict) -> str | None:
        rules = []
        if weekday_time := self.format_time(box.get("pickup_weekday")):
            distribution_day = box.get("distribution_day")
            dates = [d for d in self.emptied_dates(box) if d.weekday() < 5]
            if distribution_day == "S":
                # Every weekday
                rules.append(f"Mo-Fr {weekday_time}")
            elif distribution_day in ("X", "Y") and dates:
                # Every other weekday, alternating Mo,We,Fr and Tu,Th from one week to the next.
                first = dates[0]
                same = [DAYS[d] for d in range(first.weekday() % 2, 5, 2)]
                other = [DAYS[d] for d in range(1 - first.weekday() % 2, 5, 2)]
                if first.isocalendar().week % 2:
                    odd, even = same, other
                else:
                    odd, even = other, same
                rules.append(f"week 01-53/2 {','.join(odd)} {weekday_time}")
                rules.append(f"week 02-52/2 {','.join(even)} {weekday_time}")
            elif distribution_day and distribution_day.isdigit() and dates:
                # Fixed days each week; the listed collections span a full week.
                days = [DAYS[d] for d in sorted({d.weekday() for d in dates})]
                rules.append(f"{','.join(days)} {weekday_time}")
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/unknown_distribution_day/{distribution_day}")
        if weekend_time := self.format_time(box.get("pickup_weekend")):
            rules.append(f"Sa {weekend_time}")
        return "; ".join(rules) or None

    def closed(self, reason: str) -> None:
        missing = self.expected - self.seen
        self.crawler.stats.set_value(f"atp/{self.name}/overview_boxes", len(self.expected))
        self.crawler.stats.set_value(f"atp/{self.name}/missing_from_detail_tiles", len(missing))
        if missing:
            self.logger.warning(f"{len(missing)} boxes listed in overview tiles were not found in detail tiles")
