from typing import AsyncIterator, Iterable
from urllib.parse import urlparse

from scrapy.crawler import Crawler
from scrapy.http import Request, Response
from scrapy.item import Item


class TrackSourcesMiddleware:
    """
    Track the URLs used for each generated item,
    and overall stats per hostname.
    """

    crawler: Crawler

    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def _process_item(self, response: Response, item: Item) -> None:
        if not isinstance(item.get("extras"), dict):
            item["extras"] = {}

        if not item["extras"].get("@source_uri"):
            item["extras"]["@source_uri"] = response.url
        if not self.crawler.stats:
            return

        try:
            self.crawler.stats.inc_value(
                "atp/item_scraped_host_count/{}".format(urlparse(item["extras"]["@source_uri"]).netloc)
            )
        except ValueError:
            self.crawler.spider.logger.error(  # ty: ignore [possibly-missing-attribute]
                "Failed to parse @source_uri: {}".format(item["extras"]["@source_uri"])
            )
            self.crawler.stats.inc_value("atp/parse_error/@source_uri")

    def process_spider_output(self, response: Response, result: Iterable[Item | Request]) -> Iterable[Item | Request]:
        for x in result:
            if isinstance(x, Item):
                self._process_item(response, x)
            yield x

    async def process_spider_output_async(
        self, response: Response, result: AsyncIterator[Item | Request]
    ) -> AsyncIterator[Item | Request]:
        async for x in result:
            if isinstance(x, Item):
                self._process_item(response, x)
            yield x
