import hashlib
import json
import uuid
from typing import Any

from scrapy.exporters import JsonLinesItemExporter
from scrapy.item import Item

from locations.exporters.geojson import item_to_geometry

mapping = (
    ("housenumber", "number"),
    ("street", "street"),
    ("addr:unit", "unit"),
    ("city", "city"),
    (None, "district"),
    ("state", "region"),
    ("postcode", "postcode"),
    ("ref", "id"),
    (None, "accuracy"),
)


def item_to_properties(item: Item) -> dict[str, Any]:
    props = {}
    for map_from, map_to in mapping:
        if map_from is None:
            props[map_to] = ""
        elif map_to == "id":
            props[map_to] = str(item.get(map_from) or "")
        elif map_from in item.fields:
            props[map_to] = item.get(map_from) or ""
        else:
            props[map_to] = item["extras"].get(map_from) or ""

    return props


def compute_hash(props: dict, fingerprint: str) -> str:
    h = hashlib.sha1(fingerprint.encode("utf8"))
    h.update(json.dumps(sorted(props.items()), separators=(",", ":")).encode("utf8"))
    return h.hexdigest()[:16]


class OpenAddressesExporter(JsonLinesItemExporter):
    def _get_serialized_fields(self, item, default_value=None, include_empty=None):
        props = item_to_properties(item)

        return [
            ("type", "Feature"),
            ("properties", {"hash": compute_hash(props, str(uuid.uuid4()))} | props),
            ("geometry", item_to_geometry(item)),
        ]
