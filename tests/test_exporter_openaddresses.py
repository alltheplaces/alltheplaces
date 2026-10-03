from locations.exporters.openaddresses import compute_hash, item_to_properties
from locations.items import Feature


def test_item_to_properties():
    item = Feature()
    item["street"] = "Forelands Field Road"
    item["housenumber"] = "32"
    item["postcode"] = "PO35 5TR"
    item["city"] = "Bembridge"

    assert item_to_properties(item) == {
        "number": "32",
        "street": "Forelands Field Road",
        "unit": "",
        "city": "Bembridge",
        "district": "",
        "region": "",
        "postcode": "PO35 5TR",
        "id": "",
        "accuracy": "",
    }


def test_hash():
    item = Feature()
    item["street"] = "Forelands Field Road"
    item["housenumber"] = "32"
    item["postcode"] = "PO35 5TR"
    item["city"] = "Bembridge"

    assert compute_hash(item_to_properties(item), "457f15bf-1843-4054-b737-8d2719c641db") == "4ab9fc09b8c9a3c9"


def test_unexpected_fields_are_dropped():
    item = Feature()
    item["name"] = "Test Name"

    assert "name" not in item_to_properties(item)


def test_extras_mapped():
    item = Feature()
    item["extras"]["addr:unit"] = "Unit 1"

    assert item_to_properties(item).get("unit") == "Unit 1"
