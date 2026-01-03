from scrapy import Request, Spider
from scrapy.http import Response
from scrapy.spidermiddlewares.base import BaseSpiderMiddleware


class CDNStatsMiddleware(BaseSpiderMiddleware):
    """
    Collect response status code stats for known CDNs.
    """

    def process_response(self, request: Request, response: Response, spider: Spider):
        if not self.crawler or not self.crawler.stats:
            return response
        if response.headers.get(b"Server") == b"cloudflare":
            self.crawler.stats.inc_value("atp/cdn/cloudflare/response_count")
            self.crawler.stats.inc_value(f"atp/cdn/cloudflare/response_status_count/{response.status}")
        elif response.headers.get(b"Server") == b"AkamaiGHost":
            self.crawler.stats.inc_value("atp/cdn/akamai/response_count")
            self.crawler.stats.inc_value(f"atp/cdn/akamai/response_status_count/{response.status}")
        elif response.headers.get(b"Server") == b"CloudFront":
            self.crawler.stats.inc_value("atp/cdn/cloudfront/response_count")
            self.crawler.stats.inc_value(f"atp/cdn/cloudfront/response_status_count/{response.status}")
        return response
