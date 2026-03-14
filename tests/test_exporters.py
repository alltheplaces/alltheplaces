import io
import os
import tempfile

from locations.exporters.geojson import GeoJsonExporter, item_to_properties
from locations.exporters.geoparquet import GeoparquetExporter
from locations.exporters.ld_geojson import LineDelimitedGeoJsonExporter
from locations.items import Feature, add_social_media, set_lat_lon


def test_item_to_properties():
    item = Feature()
    item["ref"] = "a"
    item["name"] = ""

    assert item_to_properties(item) == {"ref": "a"}

    item["extras"]["b"] = "b"

    assert item_to_properties(item) == {"ref": "a", "b": "b"}

    item["extras"]["b"] = ""

    assert item_to_properties(item) == {"ref": "a"}


def test_none_values():
    item = Feature()
    values = ["0", 0, 0.0, float(0)]

    for i, v in enumerate(values):
        item["extras"][str(i)] = v

    props = item_to_properties(item)

    for i, v in enumerate(values):
        assert props[str(i)] == v

    item["extras"]["real_none"] = None

    assert "real_none" not in item_to_properties(item)


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


def test_geoparquet_exporter_with_file_path():
    """Test that geoparquet exporter works with file paths"""
    item = Feature()
    item["name"] = "Test Location"
    item["ref"] = "test_ref_1"
    set_lat_lon(item, 40.7128, -74.0060)

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        temp_file = f.name

    try:
        exporter = GeoparquetExporter(temp_file)
        exporter.export_item(item)
        exporter.finish_exporting()

        assert os.path.exists(temp_file), "Parquet file was not created"
        assert os.path.getsize(temp_file) > 0, "Parquet file is empty"

        # Verify we can read it back
        import geopandas

        gdf = geopandas.read_parquet(temp_file)
        assert len(gdf) == 1, "Parquet file should contain 1 row"
        assert gdf.iloc[0]["name"] == "Test Location"
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_geoparquet_exporter_with_file_handle():
    """Test that geoparquet exporter works with file handles (as Scrapy uses them)"""
    item = Feature()
    item["name"] = "Test Location"
    item["ref"] = "test_ref_1"
    set_lat_lon(item, 40.7128, -74.0060)

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        temp_file = f.name

    try:
        with open(temp_file, "wb") as f:
            exporter = GeoparquetExporter(f)
            exporter.export_item(item)
            exporter.finish_exporting()

        assert os.path.exists(temp_file), "Parquet file was not created"
        assert os.path.getsize(temp_file) > 0, "Parquet file is empty"

        # Verify we can read it back
        import geopandas

        gdf = geopandas.read_parquet(temp_file)
        assert len(gdf) == 1, "Parquet file should contain 1 row"
        assert gdf.iloc[0]["name"] == "Test Location"
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_geoparquet_exporter_with_bytesio():
    """Test that geoparquet exporter works with BytesIO"""
    item = Feature()
    item["name"] = "Test Location"
    item["ref"] = "test_ref_1"
    set_lat_lon(item, 40.7128, -74.0060)

    output = io.BytesIO()
    exporter = GeoparquetExporter(output)
    exporter.export_item(item)
    exporter.finish_exporting()

    assert len(output.getvalue()) > 0, "BytesIO output should not be empty"
