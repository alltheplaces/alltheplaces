from scrapy.utils.test import get_crawler

from locations.items import Feature
from locations.pipelines.state_clean_up import StateCodeCleanUpPipeline
from locations.spiders.greggs_gb import GreggsGBSpider


def get_objects():
    crawler = get_crawler(GreggsGBSpider)
    crawler.spider = crawler._create_spider()
    return Feature(), StateCodeCleanUpPipeline(crawler), crawler.spider


def test_state_name_to_code():
    item, pipeline, spider = get_objects()
    item["country"] = "CA"
    item["state"] = "Alberta"
    pipeline.process_item(item)
    assert item["state"] == "AB"

    item = Feature()
    item["country"] = "US"
    item["state"] = "California"
    pipeline.process_item(item)
    assert item["state"] == "CA"


def test_coords_to_state():
    item, pipeline, spider = get_objects()
    item["country"] = "CA"
    item["lat"], item["lon"] = 43, -80
    pipeline.process_item(item)
    assert item["state"] == "ON"

    item = Feature()
    item["country"] = "US"
    item["geometry"] = {"type": "Point", "coordinates": [-97, 31]}
    pipeline.process_item(item)
    assert item["state"] == "TX"


def test_bad_state():
    item, pipeline, spider = get_objects()
    item["country"] = "CA"
    item["state"] = "XX"
    item["lat"], item["lon"] = 43, -80
    pipeline.process_item(item)
    assert item["state"] == "ON"

    item = Feature()
    item["country"] = "US"
    item["state"] = "XX"
    item["geometry"] = {"type": "Point", "coordinates": [-97, 31]}
    pipeline.process_item(item)
    assert item["state"] == "TX"

    item = Feature()
    item["country"] = "CA"
    item["state"] = "XX"
    pipeline.process_item(item)
    assert not item["state"]

    item = Feature()
    item["country"] = "US"
    item["state"] = "XX"
    pipeline.process_item(item)
    assert not item["state"]


def test_good_state():
    item, pipeline, spider = get_objects()
    for state in ["CA", "DC", "TX"]:
        item["country"] = "US"
        item["state"] = state
        pipeline.process_item(item)
        assert item["state"] == state
