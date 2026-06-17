from locations.items import Feature
from locations.pipelines.geojson_multipoint_simplification import GeoJSONMultiPointSimplificationPipeline


def get_objects():
    return Feature(), GeoJSONMultiPointSimplificationPipeline()


def test_single_coordinate_multipoint():
    item, pipeline = get_objects()
    item["geometry"] = {"type": "MultiPoint", "coordinates": [[12.34, 56.78]]}
    pipeline.process_item(item)
    assert item["geometry"]["type"] == "Point"
    assert item["geometry"]["coordinates"][0] == 12.34
    assert item["geometry"]["coordinates"][1] == 56.78


def test_multi_coordinate_multipoint():
    item, pipeline = get_objects()
    item["geometry"] = {"type": "MultiPoint", "coordinates": [[12.34, 56.78], [-12.34, -56.78]]}
    pipeline.process_item(item)
    assert item["geometry"]["type"] == "MultiPoint"
    assert len(item["geometry"]["coordinates"]) == 2
    assert item["geometry"]["coordinates"][0][0] == 12.34
    assert item["geometry"]["coordinates"][0][1] == 56.78
    assert item["geometry"]["coordinates"][1][0] == -12.34
    assert item["geometry"]["coordinates"][1][1] == -56.78


def test_undefined_geometry():
    item, pipeline = get_objects()
    pipeline.process_item(item)
    assert item.get("geometry") is None


def test_blank_geometry():
    item, pipeline = get_objects()
    item["geometry"] = None
    pipeline.process_item(item)
    assert item.get("geometry") is None
