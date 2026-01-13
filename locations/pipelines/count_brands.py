from scrapy.crawler import Crawler

from locations.items import Feature


class CountBrandsPipeline:
    crawler: Crawler

    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_item(self, item: Feature):
        if brand := item.get("brand"):
            self.crawler.stats.inc_value(f"atp/brand/{brand}")  # ty: ignore[possibly-missing-attribute]
        if wikidata := item.get("brand_wikidata"):
            self.crawler.stats.inc_value(f"atp/brand_wikidata/{wikidata}")  # ty: ignore[possibly-missing-attribute]
        return item
