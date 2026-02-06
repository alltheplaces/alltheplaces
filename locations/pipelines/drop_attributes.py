from scrapy.crawler import Crawler

from locations.items import Feature


class DropAttributesPipeline:
    crawler: Crawler

    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_item(self, item: Feature):
        if not hasattr(self.crawler.spider, "drop_attributes"):
            return item

        for attribute in getattr(self.crawler.spider, "drop_attributes"):
            if attribute in item.fields:
                item.pop(attribute, None)
            else:
                item["extras"].pop(attribute, None)

        return item
