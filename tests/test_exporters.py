from locations.exporters.geojson import GeoJsonExporter, item_to_properties
from locations.exporters.ld_geojson import LineDelimitedGeoJsonExporter
from locations.items import Feature, add_social_media


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


def test_item_socials():
    item = Feature()
    item["ref"] = "a"
    add_social_media(item, "facebook", "abc")
    assert item["facebook"] == "abc"

    add_social_media(item, "instagram", "abc")
    assert item["extras"]["contact:instagram"] == "abc"

    assert item_to_properties(item) == {"ref": "a", "contact:facebook": "abc", "contact:instagram": "abc"}
