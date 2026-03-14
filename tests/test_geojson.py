from locations.exporters.geojson import item_to_geometry, item_to_properties
from locations.items import Feature


def test_item_to_properties():
    # Test with a feature that has some properties
    item = Feature()
    item["name"] = "Test Name"
    # We have manual mapping for some specific properties
    item["addr_full"] = "123 Test St"
    item["street"] = "Test St"
    item["housenumber"] = "123"
    item["postcode"] = "12345"
    item["city"] = "Test City"
    item["state"] = "Test State"
    item["country"] = "Test Country"
    item["twitter"] = "test_twitter"
    item["facebook"] = "test_facebook"
    item["brand_wikidata"] = "Q123456"
    item["located_in_wikidata"] = "Q654321"
    # Ref should get converted to string
    item["ref"] = 123
    # This should get added alongside the other properties. Empty and null values should be ignored
    item["extras"] = {"key1": "value1", "key2": "value2", "key3": None, "key4": ""}
    properties = item_to_properties(item)
    assert properties == {
        "name": "Test Name",
        "addr:full": "123 Test St",
        "addr:street": "Test St",
        "addr:housenumber": "123",
        "addr:postcode": "12345",
        "addr:city": "Test City",
        "addr:state": "Test State",
        "addr:country": "Test Country",
        "contact:twitter": "test_twitter",
        "contact:facebook": "test_facebook",
        "brand:wikidata": "Q123456",
        "located_in:wikidata": "Q654321",
        "key1": "value1",
        "key2": "value2",
        "ref": "123",
    }

    # Test that empty or null values are ignored
    item = Feature()
    item["name"] = None
    item["addr_full"] = ""
    item["street"] = "Test St"
    assert item_to_properties(item) == {
        "addr:street": "Test St",
    }

    # Test with an empty feature
    item = Feature()
    properties = item_to_properties(item)
    assert properties == {}


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
