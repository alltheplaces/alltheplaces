from locations.items import GeojsonPointItem


def test_geo():
    item = GeojsonPointItem()
    assert not item.has_geo(), "should not have position set"
    item.set_geo(0, 0)
    assert not item.has_geo(), "null island is not a valid position"
    item.set_geo(1.0, 0)
    assert item.has_geo(), "one non-zero coordinate is a valid position"
    item.set_geo(2.0, 3.0)
    assert 2.0 == item["lat"]
    assert 3.0 == item["lon"]


def test_source_data():
    item = GeojsonPointItem()
    item.set_source_data()["ld_json"] = "test ld_json"
    assert "test ld_json" == item["source_data"]["ld_json"]
    item = GeojsonPointItem()
    item.set_source_data("test response")
    assert "test response" == item["source_data"]["response"]


if __name__ == "__main__":
    test_geo()
    test_source_data()
    print("Everything passed")
