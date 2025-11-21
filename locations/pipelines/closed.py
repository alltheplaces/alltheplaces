from scrapy import Spider

from locations.items import Feature


class ClosePipeline:
    closed_labels = ["closed", "coming soon"]

    def process_item(self, item: Feature, spider: Spider) -> Feature:
        # Skip when we know a feature is closed
        if item["extras"].get("end_date"):
            if spider.crawler.stats:
                spider.crawler.stats.inc_value("atp/closed_poi")
            return item

        if name := item.get("name"):
            for label in self.closed_labels:
                if label in str(name).lower():
                    spider.logger.warning(f'Found {label} in {name} ({item.get("ref")})')
                    if spider.crawler.stats:
                        spider.crawler.stats.inc_value("atp/closed_check")
                    break

        return item
