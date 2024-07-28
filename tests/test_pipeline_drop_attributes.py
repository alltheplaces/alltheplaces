from scrapy import Spider
from scrapy.crawler import Crawler

from locations.items import Feature
from locations.pipelines.drop_attributes import DropAttributesPipeline
from locations.spiders.greggs_gb import GreggsGBSpider


def get_objects() -> (Spider, DropAttributesPipeline, Feature):
    spider = GreggsGBSpider()
    spider.crawler = Crawler(GreggsGBSpider)
    spider.crawler._apply_settings()
    return spider, DropAttributesPipeline(), Feature()


def test_drop_top():
    spider, pipeline, item = get_objects()
    spider.drop_attributes = {"name"}

    item["name"] = "aaaa"

    pipeline.process_item(item, spider)
    assert item.get("name") is None


def test_drop_extras():
    spider, pipeline, item = get_objects()
    spider.drop_attributes = {"aaaa"}

    item["extras"]["aaaa"] = "aaaa"

    pipeline.process_item(item, spider)
    assert item.get("aaaa") is None and item["extras"].get("aaaa") is None


def test_drop_none():
    spider, pipeline, item = get_objects()
    spider.drop_attributes = {"name", "aaaa"}

    pipeline.process_item(item, spider)
    assert item.get("name") is None
    assert item.get("aaaa") is None and item["extras"].get("aaaa") is None

    item["name"] = None
    item["extras"]["aaaa"] = None
    pipeline.process_item(item, spider)
    assert item.get("name") is None
    assert item.get("aaaa") is None and item["extras"].get("aaaa") is None

    item["name"] = ""
    item["extras"]["aaaa"] = None
    pipeline.process_item(item, spider)
    assert item.get("name") is None
    assert item.get("aaaa") is None and item["extras"].get("aaaa") is None
