import base64
import datetime
import hashlib
import json
import uuid
from io import BytesIO, StringIO
from typing import Any, Generator, Type

from scrapy import Item, Spider
from scrapy.exporters import JsonItemExporter
from scrapy.utils.misc import walk_modules
from scrapy.utils.python import to_bytes
from scrapy.utils.spider import iter_spider_classes

from locations.extensions.add_lineage import spider_class_to_lineage
from locations.geo import extract_geojson_point_geometry
from locations.settings import SPIDER_MODULES

mapping = (
    ("addr_full", "addr:full"),
    ("housenumber", "addr:housenumber"),
    ("street", "addr:street"),
    ("street_address", "addr:street_address"),
    ("city", "addr:city"),
    ("state", "addr:state"),
    ("postcode", "addr:postcode"),
    ("country", "addr:country"),
    ("name", "name"),
    ("branch", "branch"),
    ("phone", "phone"),
    ("website", "website"),
    ("twitter", "contact:twitter"),
    ("facebook", "contact:facebook"),
    ("email", "email"),
    ("opening_hours", "opening_hours"),
    ("image", "image"),
    ("brand", "brand"),
    ("brand_wikidata", "brand:wikidata"),
    ("operator", "operator"),
    ("operator_wikidata", "operator:wikidata"),
    ("network", "network"),
    ("network_wikidata", "network:wikidata"),
    ("located_in", "located_in"),
    ("located_in_wikidata", "located_in:wikidata"),
    ("nsi_id", "nsi_id"),
)


def item_to_properties(item: Item) -> dict[str, Any]:
    props = {}

    # Ref is required, unless `no_refs = True` is set in spider
    if ref := item.get("ref"):
        props["ref"] = str(ref)

    # Add in the extra bits
    if extras := item.get("extras"):
        for key, value in extras.items():
            if value is not None and value != "":
                # Only export populated values
                props[key] = value

    # Bring in the optional stuff
    for map_from, map_to in mapping:
        if item_value := item.get(map_from):
            if item_value is not None and item_value != "":
                props[map_to] = item_value

    return props


def item_to_geometry(item: Item) -> dict | None:
    """
    Extract a GeoJSON geometry object from an Item. Point geometry and
    MultiPoint geometry with a single coordinate pair are both validated.
    Other GeoJSON geometry types (e.g. Polygon) are not validated and are
    returned as-is.

    If the Item has lat and lon attributes defined instead of a geometry
    attribute, this function will return the GeoJSON Point geometry
    equivalent.

    If point geometry is validated and found to be invalid (e.g. lat of 700)
    then this function returns None.

    :param item: Item which may have geometry defined either in the geometry
                 field, or as lat/lon fields.
    :return: GeoJSON geometry dictionary or None if no such geometry could be
             extracted.
    """
    if geometry := item.get("geometry"):
        if geojson_point := extract_geojson_point_geometry(geometry):
            return geojson_point
        else:
            if geometry.get("type") in ["MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon"]:
                return geometry
            else:
                return None
    else:
        lat_untyped = item.get("lat", None)
        lon_untyped = item.get("lon", None)
        if lat_untyped is None or lon_untyped is None:
            return None
        try:
            lat_typed = float(lat_untyped)
            lon_typed = float(lon_untyped)
        except (TypeError, ValueError):
            return None
        if lat_typed < -90.0 or lat_typed > 90.0 or lon_typed < -180.0 or lon_typed > 180.0:
            return None
        geojson_point = {
            "type": "Point",
            "coordinates": [lon_typed, lat_typed],
        }
        return geojson_point


def item_to_geojson_feature(item: Item) -> dict:
    feature = {
        "id": compute_hash(item),
        "type": "Feature",
        "properties": item_to_properties(item),
        "geometry": item_to_geometry(item),
    }

    return feature


def compute_hash(item: Item) -> str:
    ref = str(item.get("ref") or uuid.uuid1()).encode("utf8")
    sha1 = hashlib.sha1(ref)

    if spider_name := item.get("extras", {}).get("@spider"):
        sha1.update(spider_name.encode("utf8"))

    return base64.urlsafe_b64encode(sha1.digest()).decode("utf8")


def find_spider_class(spider_name: str):
    if not spider_name:
        return None
    for spider_class in iter_spider_classes_in_modules():
        if spider_name == spider_class.name:
            return spider_class
    return None


def iter_spider_classes_in_modules(modules=SPIDER_MODULES) -> Generator[Type[Spider], Any, None]:
    for mod in modules:
        for module in walk_modules(mod):
            for spider_class in iter_spider_classes(module):
                yield spider_class


def get_dataset_attributes(spider_name: str) -> dict:
    spider_class = find_spider_class(spider_name)
    dataset_attributes = getattr(spider_class, "dataset_attributes", {})
    settings = getattr(spider_class, "custom_settings", {}) or {}
    if not settings.get("ROBOTSTXT_OBEY", True):
        # See https://github.com/alltheplaces/alltheplaces/issues/4537
        dataset_attributes["spider:robots_txt"] = "ignored"
    if not dataset_attributes.get("lineage"):
        dataset_attributes["spider:lineage"] = spider_class_to_lineage(spider_class).value
    dataset_attributes["@spider"] = spider_name
    dataset_attributes["spider:collection_time"] = datetime.datetime.now().isoformat()

    return dataset_attributes


class GeoJsonExporter(JsonItemExporter):
    spider_name: str | None = None

    def __init__(self, file: BytesIO, **kwargs):
        super().__init__(file, **kwargs)

    def start_exporting(self) -> None:
        pass

    def export_item(self, item: Item) -> None:
        spider_name = item.get("extras", {}).get("@spider")
        if not spider_name:
            raise RuntimeError("Spider should have a 'name' attribute specified.")

        if self.first_item:
            self.spider_name = spider_name
            self.write_geojson_header()

        if not self.spider_name:
            raise RuntimeError(
                "Exporter expected a spider name but none was available. Check the spider has a 'name' attribute specified and is not None."
            )
        if spider_name != self.spider_name:
            # It really should not happen that a single exporter instance
            # handles output from different spiders. If it does happen,
            # we rather crash than emit GeoJSON with the wrong dataset
            # properties, which may include legally relevant license tags.
            raise ValueError(
                f"Extracted data from multiple spiders ({spider_name, self.spider_name}) cannot be written to same GeoJSON file"
            )

        super().export_item(item)

    def _get_serialized_fields(
        self, item: Item, default_value: Any = None, include_empty: bool | None = None
    ) -> list[tuple]:
        feature = [
            ("type", "Feature"),
            ("id", compute_hash(item)),
            ("properties", item_to_properties(item)),
            ("geometry", item_to_geometry(item)),
        ]

        return feature

    def write_geojson_header(self) -> None:
        if not self.spider_name:
            raise RuntimeError("Spider should have a 'name' attribute specified.")
        header = StringIO()
        header.write('{"type":"FeatureCollection","dataset_attributes":')
        json.dump(
            get_dataset_attributes(self.spider_name), header, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        )
        header.write(',"features":[\n')
        self.file.write(to_bytes(header.getvalue(), self.encoding))

    def finish_exporting(self) -> None:
        if not self.first_item:
            self.file.write(b"\n]}\n")
