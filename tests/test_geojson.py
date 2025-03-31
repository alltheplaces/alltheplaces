from locations.exporters.geojson import item_to_geometry
from locations.items import Feature


def test_item_to_properties():
    assert False


def test_item_to_geometry():
    # Feature with lat and lon set and geometry not set should create a Point geometry
    item = Feature()
    item["lat"] = 1
    item["lon"] = 2
    item["geometry"] = None
    geometry = item_to_geometry(item)
    assert geometry == {"type": "Point", "coordinates": [2.0, 1.0]}

    # Feature with lat and lon set and geometry set should use the geometry
    item = Feature()
    item["geometry"] = {"type": "Polygon", "coordinates": [[1, 2], [3, 4]]}
    geometry = item_to_geometry(item)
    assert geometry == {"type": "Polygon", "coordinates": [[1, 2], [3, 4]]}

    # Feature with lat and lon not set and geometry not set should return None
    item = Feature()
    item["lat"] = None
    item["lon"] = None
    item["geometry"] = None
    geometry = item_to_geometry(item)
    assert geometry is None

    # Feature with point geometry that is empty (invalid geo) should return None
    item = Feature()
    item["lat"] = None
    item["lon"] = None
    item["geometry"] = {"type": "Point", "coordinates": []}
    geometry = item_to_geometry(item)
    assert geometry is None
