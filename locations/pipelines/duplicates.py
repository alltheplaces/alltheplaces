import logging

from scrapy import Spider
from scrapy.exceptions import DropItem

from locations.items import Feature

logger = logging.getLogger(__name__)


class DuplicatesPipeline:
    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item: Feature, spider: Spider) -> Feature:
        if getattr(spider, "no_refs", False):
            return item

        ref = (spider.name, item["ref"])
        if ref in self.ids_seen:
            if spider.crawler.stats:
                spider.crawler.stats.inc_value("atp/duplicate_count")
            raise DropItem("Duplicate item: {}".format(item["ref"]))
        else:
            self.ids_seen.add(ref)
            return item

    def close_spider(self, spider: Spider) -> None:
        if spider.crawler.stats:
            logger.info("Dropped {} duplicate items".format(spider.crawler.stats.get_value("atp/duplicate_count", 0)))
