class CDNStatsMiddleware:
    """
    Collect response status code stats for known CDNs.
    """

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        self.crawler = crawler

    def process_response(self, request, response, spider):
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
