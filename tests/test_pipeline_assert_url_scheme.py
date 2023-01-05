from locations.items import Feature
from locations.pipelines import AssertURLSchemePipeline


def test_addition():
    item = Feature()
    item["image"] = "//example.org/image.png"

    pl = AssertURLSchemePipeline()
    pl.process_item(item, None)

    assert item["image"] == "https://example.org/image.png"


def test_no_action():
    item = Feature()
    item["image"] = "https://example.org/image.png"

    pl = AssertURLSchemePipeline()
    pl.process_item(item, None)

    assert item["image"] == "https://example.org/image.png"

    item["image"] = "http://example.org/image.png"

    pl.process_item(item, None)

    assert item["image"] == "http://example.org/image.png"
