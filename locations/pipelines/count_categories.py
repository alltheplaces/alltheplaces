from scrapy.crawler import Crawler

from locations.categories import get_category_tags
from locations.items import Feature


class CountCategoriesPipeline:
    crawler: Crawler

    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_item(self, item: Feature):
        if categories := get_category_tags(item):
            for k, v in sorted(categories.items()):
                self.crawler.stats.inc_value("atp/category/%s/%s" % (k, v))  # ty: ignore[possibly-missing-attribute]
                break
            if len(categories) > 1:
                self.crawler.stats.inc_value("atp/category/multiple")  # ty: ignore[possibly-missing-attribute]
        else:
            self.crawler.stats.inc_value("atp/category/missing")  # ty: ignore[possibly-missing-attribute]
        return item
