from scrapy import signals
from scrapy.crawler import Crawler


class FilterStatsExtension:
    crawler: Crawler

    def __init__(self, crawler: Crawler):
        self.crawler = crawler
        crawler.signals.connect(self.stats_spider_closing, signal=signals.spider_closed)

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def stats_spider_closing(self):
        located_in_failed_min = int(self.crawler.settings.get("STATS_FILTER_LOCATED_IN_FAILED_MIN", 50))
        if not self.crawler.stats:
            return
        for k, v in self.crawler.stats.get_stats().copy().items():
            if k.startswith("atp/located_in_failed/"):
                if v < located_in_failed_min:
                    self.crawler.stats._stats.pop(k)
