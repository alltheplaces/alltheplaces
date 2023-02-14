from locations.exporters import GeoJsonExporter, LineDelimitedGeoJsonExporter, item_to_properties
from locations.items import Feature


def test_item_to_properties():
    item = Feature()
    item["ref"] = "a"
    item["name"] = ""

    assert item_to_properties(item) == {"ref": "a"}

    item["extras"]["b"] = "b"

    assert item_to_properties(item) == {"ref": "a", "b": "b"}

    item["extras"]["b"] = ""

    assert item_to_properties(item) == {"ref": "a"}


def test_has_geom():
    def has_geom(props: []) -> bool:
        return any(k == "geometry" for k, v in props)

    item = Feature()
    geojson_exporter = GeoJsonExporter(None)
    ld_geojson_exporter = LineDelimitedGeoJsonExporter(None)

    assert has_geom(geojson_exporter._get_serialized_fields(item))
    assert has_geom(ld_geojson_exporter._get_serialized_fields(item))

    item["lat"] = item["lon"] = 1

    assert has_geom(geojson_exporter._get_serialized_fields(item))
    assert has_geom(ld_geojson_exporter._get_serialized_fields(item))

    item["lat"] = item["lon"] = 0

    assert has_geom(geojson_exporter._get_serialized_fields(item))
    assert has_geom(ld_geojson_exporter._get_serialized_fields(item))
