from scrapy.crawler import Crawler

from locations.items import Feature


class ApplySpiderNamePipeline:
    crawler: Crawler

    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_item(self, item: Feature):
        existing_extras = item.get("extras", {})
        existing_extras["@spider"] = self.crawler.spider.name  # ty: ignore [possibly-missing-attribute]
        item["extras"] = existing_extras

        return item
