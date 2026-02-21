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
        if not self.crawler.stats:
            raise RuntimeError(
                "CountBrands pipeline cannot operate and has no effect as the Scrapy crawler has no stats collector instantiated."
            )
            return item
        if brand := item.get("brand"):
            self.crawler.stats.inc_value(f"atp/brand/{brand}")
        if wikidata := item.get("brand_wikidata"):
            self.crawler.stats.inc_value(f"atp/brand_wikidata/{wikidata}")
        return item
