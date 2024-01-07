from datetime import datetime

from locations.items import Feature, set_closed


def test_unknown():
    item = Feature()
    set_closed(item)
    assert item["extras"]["end_date"]
    assert item["extras"]["end_date"] == "yes"


def test_date():
    item = Feature()
    set_closed(item, datetime(2023, 12, 31))
    assert item["extras"]["end_date"]
    assert item["extras"]["end_date"] == "2023-12-31"
