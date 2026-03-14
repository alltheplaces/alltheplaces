from locations.items import Feature
from locations.pipelines.assert_url_scheme import AssertURLSchemePipeline


def test_addition():
    item = Feature()
    item["image"] = "//example.org/image.png"

    pl = AssertURLSchemePipeline()
    pl.process_item(item)

    assert item["image"] == "https://example.org/image.png"


def test_no_action():
    item = Feature()
    item["image"] = "https://example.org/image.png"

    pl = AssertURLSchemePipeline()
    pl.process_item(item)

    assert item["image"] == "https://example.org/image.png"

    item["image"] = "http://example.org/image.png"

    pl.process_item(item)

    assert item["image"] == "http://example.org/image.png"
