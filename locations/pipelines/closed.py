from scrapy.crawler import Crawler

from locations.items import Feature


class ClosePipeline:
    crawler: Crawler

    closed_labels = ["closed", "coming soon"]

    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_item(self, item: Feature) -> Feature:
        # Skip when we know a feature is closed
        if item["extras"].get("end_date"):
            if self.crawler.stats:
                self.crawler.stats.inc_value("atp/closed_poi")
            return item

        if name := item.get("name"):
            for label in self.closed_labels:
                if label in str(name).lower():
                    self.crawler.spider.logger.warning(  # ty: ignore[possibly-missing-attribute]
                        f'Found {label} in {name} ({item.get("ref")})'
                    )
                    if self.crawler.stats:
                        self.crawler.stats.inc_value("atp/closed_check")
                    break

        return item
