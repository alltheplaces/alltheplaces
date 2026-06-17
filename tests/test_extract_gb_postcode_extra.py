from locations.items import Feature
from locations.pipelines.extract_gb_postcode import ExtractGBPostcodePipeline, extract_gb_postcode


def test_no_addr_full_leaves_postcode_missing():
    item = Feature()
    item["country"] = "GB"

    pl = ExtractGBPostcodePipeline()
    pl.process_item(item)

    assert item.get("postcode") is None


def test_existing_postcode_not_overwritten():
    item = Feature()
    item["country"] = "GB"
    item["addr_full"] = "Somewhere, LONDON, SW1A 1AA"
    item["postcode"] = "PRESET"

    pl = ExtractGBPostcodePipeline()
    pl.process_item(item)

    assert item["postcode"] == "PRESET"


def test_extract_gb_postcode_returns_none_when_no_match():
    assert extract_gb_postcode("no postcode here") is None


def test_process_item_accepts_spider_argument():
    item = Feature()
    item["country"] = "GB"
    item["addr_full"] = "10 Downing St, London SW1A 2AA"

    class DummySpider:
        pass

    pl = ExtractGBPostcodePipeline()
    pl.process_item(item, spider=DummySpider())

    assert item["postcode"] == "SW1A 2AA"
