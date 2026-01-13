import logging

from scrapy.crawler import Crawler
from scrapy.exceptions import DropItem

from locations.items import Feature

logger = logging.getLogger(__name__)


class DuplicatesPipeline:
    crawler: Crawler

    def __init__(self, crawler: Crawler):
        self.ids_seen = set()
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_item(self, item: Feature) -> Feature:
        if getattr(self.crawler.spider, "no_refs", False):
            return item

        ref = (self.crawler.spider.name, item["ref"])  # ty: ignore[possibly-missing-attribute]
        if ref in self.ids_seen:
            if self.crawler.stats:
                self.crawler.stats.inc_value("atp/duplicate_count")
            raise DropItem("Duplicate item: {}".format(item["ref"]))
        else:
            self.ids_seen.add(ref)
            return item

    def close_spider(self) -> None:
        if self.crawler.stats:
            logger.info("Dropped {} duplicate items".format(self.crawler.stats.get_value("atp/duplicate_count", 0)))
