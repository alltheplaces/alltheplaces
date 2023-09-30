import re

from scrapy import Request, Spider
from scrapy.crawler import Crawler


def get_proxy_location(requires_proxy: bool | str, spider_name) -> str | None:
    """
    Get the country to proxy from
    :param requires_proxy: True or country code from the spider
    :param spider_name:
    :return: 2-Letter country code, or None when there is no data
    """
    if isinstance(requires_proxy, str):
        return requires_proxy
    if m := re.match(r".*_(\w{2})$", spider_name):
        return m.group(1)
    return None


class ZyteApiByCountryMiddleware:
    """
    This middleware directs requests to the Zyte API
    according to the spider's requires_proxy attribute.
    """

    zyte_api_automap = None

    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def _load_config(self, spider: Spider):
        if requires_proxy := getattr(spider, "requires_proxy", False):
            if cc := get_proxy_location(requires_proxy, spider.name):
                self.zyte_api_automap = {"geolocation": cc.upper()}  # Use the country code set in spider
            else:
                self.zyte_api_automap = True  # Let zyte work out the best place
        else:
            self.zyte_api_automap = False  # Proxy disabled

    def process_request(self, request: Request, spider: Spider):
        # Calculate zyte_api_automap on the first request
        if self.zyte_api_automap is None:
            self._load_config(spider)

        request.meta["zyte_api_automap"] = self.zyte_api_automap
