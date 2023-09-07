import logging

from scrapy.exceptions import DropItem

logger = logging.getLogger(__name__)


class DuplicatesPipeline:
    def __init__(self):
        self.ids_seen = set()
        self.duplicate_count = 0

    def process_item(self, item, spider):
        if getattr(spider, "no_refs", False):
            return item

        ref = (spider.name, item["ref"])
        if ref in self.ids_seen:
            self.duplicate_count = self.duplicate_count + 1
            raise DropItem()
        else:
            self.ids_seen.add(ref)
            return item

    def close_spider(self, spider):
        logger.info(f"Dropped {self.duplicate_count} duplicate items")
