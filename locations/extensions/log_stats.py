import datetime
import json

from scrapy import signals
from scrapy.crawler import Crawler


class LogStatsExtension:
    """
    Enable this extension to log Scrapy stats to a file at the end of the crawl,
    specified by "-s LOGSTATS_FILE=filename.json" to the scrapy command
    """

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        ext = cls(crawler)
        # crawler.signals.connect(ext.spider_opened,
        #                         signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_error)
        return ext

    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    def spider_closed(self):
        filename = None
        if self.crawler.settings and isinstance(self.crawler.settings.get("LOGSTATS_FILE"), str):
            filename = self.crawler.settings["LOGSTATS_FILE"]

        def myconverter(o):
            if isinstance(o, datetime.datetime):
                return o.isoformat()

        if filename and self.crawler.stats:
            with open(filename, "w") as f:
                f.write(
                    json.dumps(
                        self.crawler.stats.get_stats(),
                        default=myconverter,
                        sort_keys=True,
                        indent=1,
                    )
                )
