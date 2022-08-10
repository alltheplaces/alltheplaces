from locations.items import GeojsonPointItem
from locations.pipelines import AssertURLSchemePipeline


def test_addition():
    item = GeojsonPointItem()
    item["image"] = "//example.org/image.png"

    pl = AssertURLSchemePipeline()
    pl.process_item(item, None)

    assert item["image"] == "https://example.org/image.png"


def test_no_action():
    item = GeojsonPointItem()
    item["image"] = "https://example.org/image.png"

    pl = AssertURLSchemePipeline()
    pl.process_item(item, None)

    assert item["image"] == "https://example.org/image.png"

    item["image"] = "http://example.org/image.png"

    pl.process_item(item, None)

    assert item["image"] == "http://example.org/image.png"
