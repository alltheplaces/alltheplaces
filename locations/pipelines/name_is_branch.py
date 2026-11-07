from scrapy.crawler import Crawler

from locations.items import Feature


class NameIsBranchPipeline:
    crawler: Crawler

    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_item(self, item: Feature):
        if not getattr(self.crawler.spider, "name_is_branch", False):
            return item

        if item.get("name") and not item.get("branch"):
            item["branch"] = item.pop("name")

        return item
