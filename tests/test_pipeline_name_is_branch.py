from scrapy import Spider
from scrapy.utils.spider import DefaultSpider
from scrapy.utils.test import get_crawler

from locations.items import Feature
from locations.pipelines.name_is_branch import NameIsBranchPipeline


def get_objects() -> tuple[Spider, NameIsBranchPipeline, Feature]:
    crawler = get_crawler(DefaultSpider)
    crawler.spider = crawler._create_spider()
    return crawler.spider, NameIsBranchPipeline(crawler), Feature()


def test_name_moved_to_branch():
    spider, pipeline, item = get_objects()
    spider.name_is_branch = True

    item["name"] = "Downtown"

    pipeline.process_item(item)
    assert item.get("name") is None
    assert item["branch"] == "Downtown"


def test_disabled_by_default():
    spider, pipeline, item = get_objects()

    item["name"] = "Downtown"

    pipeline.process_item(item)
    assert item["name"] == "Downtown"
    assert item.get("branch") is None


def test_existing_branch_is_kept():
    spider, pipeline, item = get_objects()
    spider.name_is_branch = True

    item["name"] = "Downtown"
    item["branch"] = "Main Street"

    pipeline.process_item(item)
    assert item["name"] == "Downtown"
    assert item["branch"] == "Main Street"


def test_no_name():
    spider, pipeline, item = get_objects()
    spider.name_is_branch = True

    pipeline.process_item(item)
    assert item.get("name") is None
    assert item.get("branch") is None
