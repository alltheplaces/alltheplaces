from scrapy import Request, Spider
from scrapy.exceptions import IgnoreRequest
from scrapy.http import Response

from locations.middlewares.anti_bot_detection import AntiBotDetectionMiddleware, AntiBotMethods

class AntiBotStopCrawlMiddleware:
    def __init__(self, crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_response(self, request: Request, response: Response, spider: Spider):
        if anti_bot_methods := getattr(spider, "anti_bot_methods", None):
            nonbypassable_anti_bot_methods = [anti_bot_method for anti_bot_method in anti_bot_methods if not anti_bot_method.value["zyte_bypassable"]]
            if len(nonbypassable_anti_bot_methods) > 0 or not getattr(spider, "requires_proxy", None):
                self.close_spider(anti_bot_methods, spider)
        return response

    @staticmethod
    def close_spider(anti_bot_methods: list[AntiBotMethods], spider: Spider):
        anti_bot_names = " and ".join([anti_bot_method.value["name"] for anti_bot_method in anti_bot_methods])
        error_string = f"{anti_bot_names} anti-bot protection has been detected when executing spider {spider.name}. This spider has been halted as no bypass is currently implemented."
        spider.logger.error(error_string)
        # The CloseSpider exception doesn't work from middlewares
        # as this is not implemented in Scrapy per:
        # https://github.com/scrapy/scrapy/issues/2578
        # Instead, the following workaround makes a deferred
        # request to stop the spider. Note that many requests may
        # already have been made and this deferred request won't
        # stop those requests being handled by Scrapy. The deferred
        # stop request prevents new requests being scheduled.
        # The process_response method is then expected to raise an
        # IgnoreRequest exception.
        spider.crawler.engine.close_spider(spider, reason=error_string)
        raise IgnoreRequest(error_string)
