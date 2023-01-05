import base64
import hashlib
import io
import json
import logging
import uuid

from scrapy.exporters import JsonItemExporter, JsonLinesItemExporter
from scrapy.utils.misc import walk_modules
from scrapy.utils.python import to_bytes
from scrapy.utils.spider import iter_spider_classes

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
    ("phone", "phone"),
    ("website", "website"),
    ("twitter", "contact:twitter"),
    ("facebook", "contact:facebook"),
    ("email", "contact:email"),
    ("opening_hours", "opening_hours"),
    ("image", "image"),
    ("brand", "brand"),
    ("brand_wikidata", "brand:wikidata"),
    ("located_in", "located_in"),
    ("located_in_wikidata", "located_in:wikidata"),
    ("nsi_id", "nsi_id"),
)


def item_to_properties(item):
    props = {}

    # Ref is required, unless `no_refs = True` is set in spider
    if ref := item.get("ref"):
        props["ref"] = str(ref)

    # Add in the extra bits
    extras = item.get("extras")
    if extras:
        props.update(extras)

    # Bring in the optional stuff
    for map_from, map_to in mapping:
        item_value = item.get(map_from)
        if item_value:
            props[map_to] = item_value

    return props


def compute_hash(item):
    ref = str(item.get("ref") or uuid.uuid1()).encode("utf8")
    sha1 = hashlib.sha1(ref)

    spider_name = item.get("extras", {}).get("@spider")
    if spider_name:
        sha1.update(spider_name.encode("utf8"))

    return base64.urlsafe_b64encode(sha1.digest()).decode("utf8")


class LineDelimitedGeoJsonExporter(JsonLinesItemExporter):
    def _get_serialized_fields(self, item, default_value=None, include_empty=None):
        feature = []
        feature.append(("type", "Feature"))
        feature.append(("id", compute_hash(item)))
        feature.append(("properties", item_to_properties(item)))

        lat = item.get("lat")
        lon = item.get("lon")
        if lat and lon:
            try:
                feature.append(
                    (
                        "geometry",
                        {
                            "type": "Point",
                            "coordinates": [float(item["lon"]), float(item["lat"])],
                        },
                    )
                )
            except ValueError:
                logging.warning("Couldn't convert lat (%s) and lon (%s) to string", lat, lon)

        return feature


class GeoJsonExporter(JsonItemExporter):
    def __init__(self, file, **kwargs):
        super().__init__(file, **kwargs)
        self.spider_name = None

    def start_exporting(self):
        pass

    def export_item(self, item):
        if spider_name := item.get("extras", {}).get("@spider"):
            if self.spider_name is None:
                self.spider_name = spider_name
                self.write_geojson_header()
            if spider_name != self.spider_name:
                # It really should not happen that a single exporter instance
                # handles output from different spiders. If it does happen,
                # we rather crash than emit GeoJSON with the wrong dataset
                # properties, which may include legally relevant license tags.
                raise ValueError(
                    f"harvest from multiple spiders ({spider_name, self.spider_name}) cannot be written to same GeoJSON file"
                )

        super().export_item(item)

    def _get_serialized_fields(self, item, default_value=None, include_empty=None):
        feature = []
        feature.append(("type", "Feature"))
        feature.append(("id", compute_hash(item)))
        feature.append(("properties", item_to_properties(item)))

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
                logging.warning("Couldn't convert lat (%s) and lon (%s) to float", lat, lon)
        if geometry:
            feature.append(("geometry", geometry))

        return feature

    def write_geojson_header(self):
        header = io.StringIO()
        header.write('{"type":"FeatureCollection","properties":')
        props = {"@spider": self.spider_name} if self.spider_name else {}
        if spider := self.find_spider_class(self.spider_name):
            props.update(getattr(spider, "dataset_attributes", {}))
            settings = getattr(spider, "custom_settings", {}) or {}
            if not settings.get("ROBOTSTXT_OBEY", True):
                # See https://github.com/alltheplaces/alltheplaces/issues/4537
                props["spider:robots_txt"] = "ignored"
        json.dump(props, header, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        header.write(',"features":[\n')
        self.file.write(to_bytes(header.getvalue(), self.encoding))

    def finish_exporting(self):
        self.file.write(b"\n]}\n")

    @staticmethod
    def find_spider_class(spider_name):
        for module in walk_modules("locations.spiders"):
            for spider_class in iter_spider_classes(module):
                if spider_name == spider_class.name:
                    return spider_class
        return None
