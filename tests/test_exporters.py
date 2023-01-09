from locations.exporters import item_to_properties
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
