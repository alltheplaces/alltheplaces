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
        spider_name = getattr(self.crawler.spider, "name", False)
        if not isinstance(spider_name, str):
            raise RuntimeError("Spider is missing a 'name' attribute. ApplySpiderName pipeline cannot operate.")

        existing_extras = item.get("extras", {})
        existing_extras["@spider"] = spider_name
        item["extras"] = existing_extras

        return item
