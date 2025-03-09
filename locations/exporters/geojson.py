from base64 import urlsafe_b64encode
from datetime import datetime
from hashlib import sha1
from io import StringIO
from json import dump
from logging import warning
from random import randbytes
from typing import Any

from scrapy import Item
from scrapy.exporters import JsonItemExporter
from scrapy.utils.python import to_bytes

from locations.items import Feature

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
            if value is not None and value != "" and key != "@spider" and key != "@spider_classes":
                # Only export populated values and ignore certain attributes
                # which are output in the GeoJSON header as
                # non-feature-specific attributes.
                props[key] = value

    # Bring in the optional stuff
    for map_from, map_to in mapping:
        if item_value := item.get(map_from):
            if item_value is not None and item_value != "":
                props[map_to] = item_value

    return props


def item_to_geometry(item: Item) -> dict:
    """
    Convert the item to a GeoJSON geometry object. If the item has lat and lon fields,
    but no geometry field, then a Point geometry will be created. Otherwise the
    geometry field will be returned as is.

    :param item: The scraped item.
    :return: The GeoJSON geometry object.
    """

    lat = item.get("lat")
    lon = item.get("lon")
    geometry = item.get("geometry")
    if lat and lon and not geometry:
        try:
            geometry = {
                "type": "Point",
                "coordinates": [float(item["lon"]), float(item["lat"])],
            }
        except ValueError:
            warning("Couldn't convert lat (%s) and lon (%s) to float", lat, lon)
    return geometry


def item_to_geojson_feature(item: Feature) -> dict:
    feature = {
        "id": compute_hash(item),
        "type": "Feature",
        "properties": item_to_properties(item),
        "geometry": item_to_geometry(item),
    }

    return feature


def compute_hash(item: Feature) -> str:
    item_ref = item.get("ref")
    item_spider_class = item.get("extras", {}).get("@spider_classes", [None])[0]
    item_spider_name = None
    if item_spider_class:
        item_spider_name = getattr(item_spider_class, "name", None)

    if item_ref and item_spider_name:
        sha1_hash = sha1(str(item_ref).encode("utf8"))
        sha1_hash.update(item_spider_name.encode("utf8"))
        return urlsafe_b64encode(sha1_hash.digest()).decode("utf8")

    # If a spider has no_refs = True, generate a GeoJSON feature identifier
    # as a random ID that will change each time a crawl and export is
    # completed.
    return urlsafe_b64encode(randbytes(20)).decode("utf8")


def get_dataset_attributes(spider_classes: list[type]) -> dict:
    """
    Apply dataset attributes from base classes and the class of the spider in
    reverse method resolution order, overwriting any previous value. This is
    best illustrated by an example:

    class ExampleSpider(ParentSpiderClassA, ParentSpiderClassB):
        dataset_attributes = {"attribute_a": "E", "attribute_b": "X"}

    class ParentSpiderClassA():
        dataset_attributes = {"attribute_a": "A", "attribute_c": "Y"}

    class ParentSpiderClassB():
        dataset_attributes = {"attribute_a": "B", "attribute_c": "Z"}

    For this example, this function will return the following dictionary:
        dataset_attributes = {
            "attribute_a": "E",
            "attribute_b": "X",
            "attribute_c": "Y",
        }
    """
    combined_dataset_attributes = {}
    for spider_class in reversed(spider_classes):
        dataset_attributes = getattr(spider_class, "dataset_attributes", {}) or {}
        settings = getattr(spider_class, "custom_settings", {}) or {}
        if not settings.get("ROBOTSTXT_OBEY", True):
            # See https://github.com/alltheplaces/alltheplaces/issues/4537
            dataset_attributes["spider:robots_txt"] = "ignored"
        combined_dataset_attributes.update(dataset_attributes)
    if len(spider_classes) > 0:
        if spider_name := getattr(spider_classes[0], "name", None):
            combined_dataset_attributes["@spider"] = spider_name
    combined_dataset_attributes["spider:collection_time"] = datetime.now().isoformat()
    return combined_dataset_attributes


class GeoJsonExporter(JsonItemExporter):
    def __init__(self, file, **kwargs):
        super().__init__(file, **kwargs)
        self.exporter_spider_class: type = None

    def start_exporting(self):
        pass

    def export_item(self, item: Feature):
        item_spider_classes = item.get("extras", {}).get("@spider_classes", [])
        item_spider_class = None
        if len(item_spider_classes) > 0:
            item_spider_class = item_spider_classes[0]

        if self.first_item:
            # Remember the spider class which generated the first item this
            # exporter first encounters. If this exporter then encounters an
            # item generated by a different spider class, stop exporting and
            # generate a fatal exception. It is preferred to cancel the export
            # than to omit a GeoJSON file with the wrong headers confused
            # between two or more spiders.
            self.exporter_spider_class = item_spider_class
            self.write_geojson_header(item_spider_classes)

        if item_spider_class != self.exporter_spider_class:
            raise ValueError(
                f"Items generated from multiple spiders ({item_spider_class, self.exporter_spider_class}) cannot be written to same GeoJSON file."
            )

        super().export_item(item)

    def _get_serialized_fields(self, item: Feature, default_value=None, include_empty=None):
        feature = [
            ("type", "Feature"),
            ("id", compute_hash(item)),
            ("properties", item_to_properties(item)),
            ("geometry", item_to_geometry(item)),
        ]

        return feature

    def write_geojson_header(self, spider_classes: list[type]) -> None:
        header = StringIO()
        header.write('{"type":"FeatureCollection","dataset_attributes":')
        dump(get_dataset_attributes(spider_classes), header, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        header.write(',"features":[\n')
        self.file.write(to_bytes(header.getvalue(), self.encoding))

    def finish_exporting(self):
        if not self.first_item:
            self.file.write(b"\n]}\n")
