from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from locations.exporters.geojson import find_spider_class


def test_item_attributes_type():
    settings = get_project_settings()
    process = CrawlerProcess(settings)

    for name in process.spider_loader.list():
        spider = find_spider_class(name)
        item_attributes = getattr(spider, "item_attributes", {})
        assert isinstance(item_attributes, dict)

        if extras := item_attributes.get("extras"):
            assert isinstance(extras, dict)
