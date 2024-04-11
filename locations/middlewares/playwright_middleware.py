from scrapy import Request, Spider


class PlaywrightMiddleware:
    def process_request(self, request: Request, spider: Spider):
        # If we're a playwright spider, and playwright hasn't been set on the request, default to true
        if getattr(spider, "is_playwright_spider", False):
            if "playwright" not in request.meta:
                request.meta["playwright"] = True
