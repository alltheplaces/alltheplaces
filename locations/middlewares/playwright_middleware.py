from scrapy import Request, Spider


class PlaywrightMiddleware:
    def process_request(self, request: Request, spider: Spider):
        # If we're a playwright spider, and playwright hasn't been set on the request, default to true
        if hasattr(spider, "is_playwright_spider") and getattr(spider, "is_playwright_spider"):
            if not request.meta.get("playwright"):
                request.meta["playwright"] = True
